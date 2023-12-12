# -*- coding: utf-8 -*-
"""Ex3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1hywkYXBO31Ixa4mtBCAmVbcjdfR-86y4

#1. Mount Google Drive
This allows the notebook to import/export data from files inside Google Drive.
"""

from google.colab import drive
drive.mount('/content/drive')

"""#2. Install ViZDoom and additional libraries

ViZDoom is the platform used to train the agents.
Stable-Baselines3 is a library specific for reinforcement learning agents.
"""

!sudo apt update
!sudo apt upgrade

!sudo apt install cmake libboost-all-dev libsdl2-dev libfreetype6-dev libgl1-mesa-dev libglu1-mesa-dev libpng-dev libjpeg-dev libbz2-dev libfluidsynth-dev libgme-dev libopenal-dev zlib1g-dev timidity tar nasm

!pip install git+https://github.com/mwydmuch/ViZDoom
#!pip install vizdoom

!pip install stable-baselines3

!sudo apt update
!sudo apt upgrade

"""#3. Import libraries"""

from vizdoom import *
from vizdoom import Button

import numpy as np
import pandas as pd
import cv2
import math

import gym
from gym import Env
from gym import spaces

from stable_baselines3.common import vec_env
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage

import typing as t
import itertools

from stable_baselines3 import ppo
from stable_baselines3.common.vec_env import VecMonitor
from stable_baselines3.common import callbacks
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common import evaluation
from stable_baselines3.common import policies

"""#4. The ViZDoom environment

### The DoomEnvironment class

The DoomEnvironment class represents an interpreter of the ViZDoom game so the SB3-Agents can work with it.

The class handles the step process, the rewards and the creation of the agent's observation, through the capturing and processing of game frames and any other relevant data, and structuring it into a single observation.
<br>
<br>

### The create_environment() function

The create_environment() function creates an environment object, starts and returns an instance of the game.
<br>
<br>

### Possible actions
A ViZDoom agent acts on its environment through the buttons of the game. Each button represents an action. Actions may be done alone or in combination with other actions. For example, the agent is able to move around and shoot at the same time, or turn around whilst moving.

For our agent, we will limit shooting as an exclusive action. It won't be allowed to shoot while moving. Also, to limit the number of combinations available for our agent to try, as they make no sense, we will not include button combinations where mutually exclusive buttons are activated at the same time (for example, moving left and right at the same time).
"""

#Buttons combinations that can not be used together
MUTUALLY_EXCLUSIVE_BUTTON_COMBINATIONS = [
                             [Button.MOVE_FORWARD, Button.MOVE_BACKWARD],
                             [Button.MOVE_RIGHT, Button.MOVE_LEFT],
                             [Button.TURN_RIGHT, Button.TURN_LEFT]
]

#Buttons that can only be used alone
EXCLUSIVE_BUTTONS = [Button.ATTACK]

def get_exclusive_button_mask(actions: np.ndarray, buttons: np.array) -> np.array:
    exclusive_action_filter = np.isin(buttons, EXCLUSIVE_BUTTONS)
    exclusive_action_mask = (np.any(actions.astype(bool) & exclusive_action_filter, axis = -1)) & (np.sum(actions, axis = -1) > 1)
    return exclusive_action_mask

def get_mutually_exclusive_button_mask(actions: np.ndarray, buttons: np.array) -> np.array:
    mutually_exclusive_action_filter = np.array([np.isin(buttons, invalid_combination) for invalid_combination in MUTUALLY_EXCLUSIVE_BUTTON_COMBINATIONS])
    mutually_exclusive_action_mask = np.any(np.sum(
                                             (actions[:, np.newaxis, :] * mutually_exclusive_action_filter.astype(int)),
                                              axis = -1) > 1, axis = -1)
    return mutually_exclusive_action_mask

def get_available_actions(buttons: np.array) -> t.List[t.List[float]]:
    #Create list of all possible action combinations (2^n combinations, with n being the number of available buttons)
    action_combinations = np.array([list(seq) for seq in itertools.product([0.0, 1.0], repeat=len(buttons))])

    #Create a mask that filters unathorized action combinations
    action_filter_mask = (get_exclusive_button_mask(action_combinations, buttons)
                         | get_mutually_exclusive_button_mask(action_combinations, buttons))

    possible_actions = action_combinations[~action_filter_mask]
    possible_actions = possible_actions[np.sum(possible_actions, axis=1) > 0]  # Prevent idling
    return possible_actions.tolist()

Frame = np.ndarray

class DoomEnvironment (Env):
    """Wrapper environment following OpenAI's gym interface for a ViZDoom game instance."""

    def __init__(self,
                 game: DoomGame,
                 frame_skip: int = 4,
                 screen_type: int = 0,
                 limit_boxes: bool = False):
        super().__init__()

        self.game = game

        # Define some test variables
        self.screen_type = screen_type
        self.limit_boxes = limit_boxes
        self.frame_skip = frame_skip
        self.empty_frame = np.zeros((240, 320, 3), dtype=np.uint8)
        self.player_color = [255, 255, 255]
        self.monster_color = [255, 0, 0]
        self.key_color = [0, 255, 0]
        self.wall_color = [0, 0, 0]
        self.floor_obj_color = [64, 64, 64]

        self.player_x = self.game.get_game_variable(GameVariable.POSITION_X)
        self.player_y = self.game.get_game_variable(GameVariable.POSITION_Y)

        self.distance_coeff = 0
        ini_objects = self.game.get_state().objects
        ini_distance = 0
        for ini_obj in ini_objects:
            if (ini_obj.name == 'RedSkull'):
                ini_distance = self.calculate_object_distance(ini_obj.position_x, ini_obj.position_y)
        self.distance = ini_distance
        self.last_distance = ini_distance
        self.ammo_coeff = 0.1
        self.ammo = self.game.get_game_variable(GameVariable.AMMO2)
        self.last_ammo = self.ammo
        self.health_coeff = 0.5
        self.health = self.game.get_game_variable(GameVariable.HEALTH)
        self.last_health = self.health

        # Determine observation space
        self.state = self.create_observation()
        self.observation_space = spaces.Box(low = 0, high = 255, shape = self.state.shape, dtype = np.uint8)

        # Determine action space
        self.possible_actions = get_available_actions(np.array(
                                [Button.ATTACK, Button.MOVE_FORWARD, Button.MOVE_RIGHT, Button.MOVE_LEFT,
                                 Button.MOVE_BACKWARD, Button.TURN_RIGHT, Button.TURN_LEFT]))
        #self.possible_actions = np.eye(7).tolist()
        self.action_space = spaces.Discrete(len(self.possible_actions))

        return

    def reset(self) -> Frame:
        """Resets the environment.
        Returns:
            The initial state of the new environment.
        """
        self.game.new_episode()
        self.state = self.create_observation()
        return self.state

    def close(self) -> None:
        self.game.close()
        return

    def step(self, action: int) -> t.Tuple[Frame, int, bool, t.Dict]:
        """Apply an action to the environment.
        Args:
            action:
        Returns:
            A tuple containing:
                - A numpy ndarray containing the current environment state.
                - The reward obtained by applying the provided action.
                - A boolean flag indicating whether the episode has ended.
                - An empty info dict.
        """
        reward = self.game.make_action(self.possible_actions[action], self.frame_skip)
        additional_reward = self.calculate_additional_reward()
        reward = reward + additional_reward
        done = self.game.is_episode_finished()
        self.state = self.create_observation()
        return self.state, reward, done, {'kills':self.game.get_game_variable(GameVariable.KILLCOUNT),
                                          'keys':self.game.get_game_variable(GameVariable.USER4),
                                          'ammo':self.game.get_game_variable(GameVariable.AMMO2),
                                          'health':self.game.get_game_variable(GameVariable.HEALTH),
                                          'hit count':self.game.get_game_variable(GameVariable.HITCOUNT)}

    def create_observation(self):
        self.player_x = self.game.get_game_variable(GameVariable.POSITION_X)
        self.player_y = self.game.get_game_variable(GameVariable.POSITION_Y)
        screen = self.preprocess_frame()

        observation = screen
        #observation = {'screen': screen, 'data': data, 'scene_graph': scene_graph}
        return observation

    def calculate_object_distance(self, position_x, position_y):
        distance = math.sqrt(math.pow((position_x - self.player_x), 2) + math.pow((position_y - self.player_y), 2))
        return distance

    def calculate_additional_reward(self):
        additional_reward = 0
        distance_reward = 0
        ammo_reward = 0
        health_reward = 0
        if (self.game.get_state() is not None):
            objects = self.game.get_state().objects
            for obj in objects:
                if (obj.name == 'RedSkull'):
                    self.distance = self.calculate_object_distance(obj.position_x, obj.position_y)
                    distance_reward += self.distance_coeff * (self.last_distance - self.distance)
                    self.last_distance = self.distance

            self.ammo = self.game.get_game_variable(GameVariable.AMMO2)
            ammo_reward = self.ammo_coeff * (self.ammo - self.last_ammo)
            self.last_ammo = self.ammo

            self.health = self.game.get_game_variable(GameVariable.HEALTH)
            health_reward += self.health_coeff * (self.health - self.last_health)
            self.last_health = self.health

            additional_reward = distance_reward + ammo_reward + health_reward
        return additional_reward

    def preprocess_frame(self):
        """
        Preprocess frame before stacking it:
            - Region-of-interest (ROI) selected from the original frame.
            Frame is cut by 40 pixels up and down, and 30 pixels for left and right.
            - Normalize images to interval [0,1]
        """
        frame = self._get_screen_buffer_frame()
        if (self.screen_type == 1):
            frame = self._get_label_buffer_frame()

        roi = frame[40:-40, :]
        #roi = frame[40:-40, 30:-30]
        resized_roi = cv2.resize(roi, None, fx = 0.5, fy = 0.5, interpolation = cv2.INTER_AREA)
        #roi_normal = np.divide(roi, 255, dtype=np.float32)
        #print("Preprocessed new frame is", tf.shape(roi_normal), ".")
        return resized_roi

    def _get_screen_buffer_frame(self):
        """ Get the current game screen buffer or an empty screen buffer if episode is finished"""
        if (self.game.is_episode_finished()):
            return self.empty_frame
        else:
            return self.game.get_state().screen_buffer

    def _get_label_buffer_frame(self):
        """ Get the current game label screen buffer or an empty screen buffer if episode is finished"""
        if (self.game.is_episode_finished()):
            return self.empty_frame
        else:
            monster_value = 0
            key_value = 0
            labels_buffer = self.game.get_state().labels_buffer
            frame = self.empty_frame
            frame[labels_buffer == 0] = self.wall_color
            frame[labels_buffer > 0] = self.floor_obj_color
            frame[labels_buffer == 255] = self.player_color
            if (self.game.get_state().labels is not None):
                for label in self.game.get_state().labels:
                    if (label.object_name == 'RedSkull'):
                        key_value = label.value
                        frame[labels_buffer == key_value] = self.key_color
                    if (label.object_name == 'DoomImp' or label.object_name == 'Demon' or label.object_name == 'Cacodemon'):
                        monster_value = label.value
                        frame[labels_buffer == monster_value] = self.monster_color
            return frame

    def render(self, mode = 'human'):
        pass

def create_environment(scenario: str = 'basic', config: str = 'basic',
                       #resolution: ScreenResolution = ScreenResolution.RES_320x240, color_scheme: int = ScreenFormat.RGB24,
                       crosshair: bool = False, sync_mode: bool = True,
                       game_display: bool = False, **kwargs) -> DoomEnvironment:
    ### New game instance
    game = DoomGame()

    path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/'
    scenario += '.wad'
    config += '.cfg'

    ### Adjust configuration and scenario paths
    game.load_config(path+config)
    game.set_doom_scenario_path(path+scenario)

    game.set_screen_format(ScreenFormat.RGB24)
    #game.set_screen_resolution(resolution)
    #game.set_screen_format(color_scheme)

    game.set_labels_buffer_enabled(True)
    game.set_objects_info_enabled(True)

    if (sync_mode == True):
        game.set_mode(Mode.PLAYER)
    else:
        game.set_mode(Mode.ASYNC_PLAYER)
    game.set_render_crosshair(crosshair)

    ### Google Colab does not support the video output of ViZDoom. The following line is needed for the environment to be run.
    game.set_window_visible(game_display)

    #Initiate the game
    game.init()

    return DoomEnvironment(game, **kwargs)

def create_vec_env(n_envs = 1, **kwargs) -> VecTransposeImage:
    return VecTransposeImage(DummyVecEnv([lambda: create_environment(**kwargs)] * n_envs))

def create_eval_vec_env(**kwargs) -> VecTransposeImage:
    return create_vec_env(n_envs = 1, **kwargs)

"""#5. The play_env() function

This function is responsible for running an agent with agent_args parameters in a Doom game with env_args parameters.

The training data is output to a csv file containing the variables listed within the info_keywords parameter.
"""

def count_trainable_parameters(model):
    print('Number of trainable parameters: {:,}'.format(sum(p.numel() for p in model.policy.parameters() if p.requires_grad)))
    return

def play_env(env_args, agent_args, n_envs, timesteps, callbacks, log_name, eval_freq = None, init_func = None):

    csv_log_path = f'/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/Data/{log_name}'
    csv_eval_log_path = f'/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/Data/{log_name}_eval'

    #Create the environments
    env = create_vec_env(n_envs, **env_args)
    env = VecMonitor(env, csv_log_path, info_keywords=('kills', 'keys', 'ammo', 'health', 'hit count'))

    #Build the agent
    agent = ppo.PPO(policies.ActorCriticCnnPolicy, env, tensorboard_log = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/tensorboard', seed = 0, **agent_args)
    count_trainable_parameters(agent)

    #Optional processing on the agent
    if init_func is not None:
        init_func(agent)

    #Optional evalutation callback
    eval_env_args = env_args
    #eval_env_args['frame_skip'] = 1
    if eval_freq is not None:
        eval_env = create_eval_vec_env(**eval_env_args)
        eval_env = VecMonitor(eval_env, csv_eval_log_path, info_keywords=('kills', 'keys', 'ammo', 'health', 'hit count'))

        callbacks.append(EvalCallback(
                                  eval_env,
                                  n_eval_episodes = 10,
                                  eval_freq = eval_freq,
                                  log_path = f'/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/evaluations/{log_name}',
                                  best_model_save_path = f'/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/{log_name}'))

    #Train the agent
    agent.learn(total_timesteps = timesteps, tb_log_name = log_name, callback = callbacks)

    #Finishing
    env.close()
    if eval_freq is not None:
        eval_env.close()

    return agent

"""#6. GIF maker function"""

import imageio

def make_gif(agent, file_path, gif_env_args):
    env = create_vec_env(scenario = gif_env_args['scenario'],
                         config = gif_env_args['config'],
                         #resolution = gif_env_args['resolution'],
                         #color_scheme = gif_env_args['color_scheme'],
                         frame_skip = 1,
                         screen_type = gif_env_args['screen_type'],
                         limit_boxes = gif_env_args['limit_boxes'],
                         crosshair = gif_env_args['crosshair'],
                         sync_mode = gif_env_args['sync_mode'],
                         game_display = gif_env_args['game_display'])
    env.venv.envs[0].game.set_seed(0)

    images = []

    for i in range(10):
        obs = env.reset()

        done = False
        while not done:
            action, _ = agent.predict(obs)
            obs, reward, done, _ = env.step(action)
            if gif_env_args['screen_type'] == 0:
                images.append(env.venv.envs[0].game.get_state().screen_buffer)
            elif gif_env_args['screen_type'] == 1:
                label_frame = env.venv.envs[0]._get_label_buffer_frame()
                images.append(label_frame)


    imageio.mimsave(file_path, images, fps = 25)

    env.close()

"""#7. Game parameters

Parameters to be used when creating the environments, the agents and the GIFs.
"""

env_args = {
    # Scenario to play
    'scenario': 'env3',
    # Configuration file with game rules
    'config': 'env3_e',
    # Screen resolution
    #'resolution': ScreenResolution.RES_320x240,
    # Screen coloring scheme
    #'color_scheme': ScreenFormat.RGB24,
    # Number of steps for which the last action is repeated
    'frame_skip': 4,
    # Screem type
    #'screen_type': 0,
    'screen_type': 1,
    # Box representing the visual limits of each game entity
    'limit_boxes': False,
    # Render weapon crosshair?
    'crosshair': False,
    # If true, the game will be in synchronous mode, which waits for the agent to pick an action to advance the environment;
    # if false, the environment will not wait on the agent
    'sync_mode': True,
    # Game window display
    'game_display': False
}

agent_args = {
    'n_steps': 4096,
    'n_epochs': 3,
    'learning_rate': 1e-5,
    'gamma': 0.995,
    'clip_range': 0.15,
    'target_kl': 0.03,
    'ent_coef': 1e-2,
    'batch_size': 32,
    'policy_kwargs': {'features_extractor_kwargs': {'features_dim': 128}}
}

gif_env_args = {
    #Scenario to play
    'scenario': 'env3',
    #Configuration file with game rules
    'config': 'env3_e',
    # Screen resolution
    #'resolution': ScreenResolution.RES_640x480,
    # Screen coloring scheme
    #'color_scheme': ScreenFormat.RGB24,
    # Number of steps for which the last action is repeated
    'frame_skip': 1,
    # Screen type
    #'screen_type': 0,
    'screen_type': 1,
    # Box representing the visual limits of each game entity
    'limit_boxes': False,
    # Render weapon crosshair?
    'crosshair': False,
    # If true, the game will be in synchronous mode, which waits for the agent to pick an action to advance the environment;
    # if false, the environment will not wait on the agent
    'sync_mode': True,
    # Game window display
    'game_display': False
}

"""#8. Running the agents

Agents are trained according to the respective session parameters, evaluated at a set frequency, and then both the best and the final models are run for making each one GIF.
"""

#Training and playing in the environment
agent1 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels1', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels1.gif'
make_gif(agent = agent1, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels1.gif'
agent1 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels1/best_model.zip')
make_gif(agent = agent1, file_path = gif_file_path, gif_env_args = gif_env_args)

agent2 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels2', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels2.gif'
make_gif(agent = agent2, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels2.gif'
agent2 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels2/best_model.zip')
make_gif(agent = agent2, file_path = gif_file_path, gif_env_args = gif_env_args)

agent3 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels3', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels3.gif'
make_gif(agent = agent3, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels3.gif'
agent3 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels3/best_model.zip')
make_gif(agent = agent3, file_path = gif_file_path, gif_env_args = gif_env_args)

agent4 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels4', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels4.gif'
make_gif(agent = agent4, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels4.gif'
agent4 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels4/best_model.zip')
make_gif(agent = agent4, file_path = gif_file_path, gif_env_args = gif_env_args)

agent5 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels5', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels5.gif'
make_gif(agent = agent5, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels5.gif'
agent5 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels5/best_model.zip')
make_gif(agent = agent5, file_path = gif_file_path, gif_env_args = gif_env_args)

agent6 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels6', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels6.gif'
make_gif(agent = agent6, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels6.gif'
agent6 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels6/best_model.zip')
make_gif(agent = agent6, file_path = gif_file_path, gif_env_args = gif_env_args)

agent7 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels7', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels7.gif'
make_gif(agent = agent7, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels7.gif'
agent7 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels7/best_model.zip')
make_gif(agent = agent7, file_path = gif_file_path, gif_env_args = gif_env_args)

agent8 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels8', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels8.gif'
make_gif(agent = agent8, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels8.gif'
agent8 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels8/best_model.zip')
make_gif(agent = agent8, file_path = gif_file_path, gif_env_args = gif_env_args)

agent9 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels9', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels9.gif'
make_gif(agent = agent9, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels9.gif'
agent9 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels9/best_model.zip')
make_gif(agent = agent9, file_path = gif_file_path, gif_env_args = gif_env_args)

agent10 = play_env(env_args, agent_args, n_envs = 2, timesteps = 350000, callbacks = [], log_name = 'labels10', eval_freq = 25000)

gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/final-labels10.gif'
make_gif(agent = agent10, file_path = gif_file_path, gif_env_args = gif_env_args)
gif_file_path = '/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/GIFs/best-labels10.gif'
agent10 = ppo.PPO.load('/content/drive/My Drive/ViZDoom/Agents/Mestrado/Ex3/logs/models/labels10/best_model.zip')
make_gif(agent = agent10, file_path = gif_file_path, gif_env_args = gif_env_args)