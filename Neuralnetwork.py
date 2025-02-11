import random
import ast

import numpy
from keras import models, layers
import matplotlib.pyplot as plt
import Minimax
from Game import Game


def get_random_game_state_and_next_best_move(is_O):
    game = Game()

    O_moves = [1, 3, 5, 7]
    X_moves = [0, 2, 4, 6, 8]

    moves = X_moves
    if is_O:
        moves = O_moves

    random_index = random.randint(0, len(moves) - 1)
    # get random board position by playing random moves
    # if game is ending state redo the process since there is no go good next move in such a state
    while True:
        not_end_state = True
        for i in range(moves[random_index]):
            possible_moves = game.get_possible_moves()
            random_move = possible_moves[random.randint(0, len(possible_moves) - 1)]
            game.move(random_move[0], random_move[1])
            if game.is_ending_state():
                game = Game()
                not_end_state = False
                break

        if not_end_state:
            break

    best_move = Minimax.get_best_move(game)
    best_output = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    best_output[(best_move[0] + 3 * best_move[1])] = 1

    return game.get_board_value(), best_output


def generate_training_data(size, is_O, command):
    name = "X_training_data.txt"
    if is_O:
        name = "O_training_data.txt"

    if not (command == "a" or command == "w"):
        print("Error, command can only be 'w' or 'a' ")
        return

    f = open(name, command)
    for i in range(size):
        print(f"{i} of {size}")
        f.write((str(get_random_game_state_and_next_best_move(is_O))[1:-1]) + "\n")
    f.close()


def train_and_save_model(location, training_data_location):
    model = generate_model(9, [12, 14, 14, 12], 9)
    visualize_nn(model)
    model = compile_model(model)
    model = train(model, training_data_location, 300, 32)
    model.summary()
    model.save(location)


def train(model, train_data_file, epochs, batch_size):
    input_data = []
    output_data = []

    with open(train_data_file) as file:
        for line in file:
            data = ast.literal_eval(line.rstrip())
            input_data.append(data[0])
            output_data.append(data[1])

    X = numpy.array(input_data)
    y = numpy.array(output_data)
    # Train and test data split
    boundary = int(0.8 * len(X))
    X_train = X[:boundary]
    X_test = X[boundary:]
    y_train = y[:boundary]
    y_test = y[boundary:]
    training = model.fit(x=X_train, y=y_train,
                         validation_data=(X_test, y_test),
                         batch_size=batch_size, epochs=epochs,
                         shuffle=True, verbose=0,
                         validation_split=0.3)

    # plot
    metrics = [k for k in training.history.keys() if ("loss" not in k) and ("val" not in k)]
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(15, 3))

    # training
    ax[0].set(title="Training")
    ax11 = ax[0].twinx()
    ax[0].plot(training.history['loss'], color='black')
    ax[0].set_xlabel('Epochs')
    ax[0].set_ylabel('Loss', color='black')
    for metric in metrics:
        ax11.plot(training.history[metric], label=metric)
        ax11.set_ylabel("Score", color='steelblue')
    ax11.legend()

    # validation
    ax[1].set(title="Validation")
    ax22 = ax[1].twinx()
    ax[1].plot(training.history['val_loss'], color='black')
    ax[1].set_xlabel('Epochs')
    ax[1].set_ylabel('Loss', color='black')
    for metric in metrics:
        ax22.plot(training.history['val_' + metric], label=metric)
        ax22.set_ylabel("Score", color="steelblue")
    plt.show()

    return model


def get_best_move(model, game):
    board_values = game.get_board_value()
    outputs = model.predict(numpy.array(board_values).reshape(-1, 9))[0]

    best_output, best_index = outputs[0], 0
    for index, output in enumerate(outputs):
        if output > best_output and board_values[index] == 0:
            best_output = output
            best_index = index

    return best_index % 3, int(best_index / 3)


def compile_model(model):
    # compile the neural network
    model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=['accuracy'])

    return model


def generate_model(number_of_inputs, number_of_nodes_in_layers, number_of_outputs):
    # DeepNN

    # layer input
    inputs = layers.Input(name="input", shape=(number_of_inputs,))

    last_layer = inputs
    for i, number_of_nodes in enumerate(number_of_nodes_in_layers):
        # hidden layer i
        current_layer = layers.Dense(name=f"h{i}", units=number_of_nodes, activation='relu')(last_layer)
        current_layer = layers.Dropout(name=f"drop{i}", rate=0.2)(current_layer)
        last_layer = current_layer

    # layer output
    outputs = layers.Dense(name="output", units=number_of_outputs, activation='sigmoid')(last_layer)

    return models.Model(inputs=inputs, outputs=outputs, name="DeepNN")


def utils_nn_config(model):
    lst_layers = []
    if "Sequential" in str(model):
        layer = model.layers[0]
        lst_layers.append({"name": "input", "in": int(layer.input.shape[-1]), "neurons": 0,
                           "out": int(layer.input.shape[-1]), "activation": None,
                           "params": 0, "bias": 0})
    for layer in model.layers:
        try:
            dic_layer = {"name": layer.name, "in": int(layer.input.shape[-1]), "neurons": layer.units,
                         "out": int(layer.output.shape[-1]), "activation": layer.get_config()["activation"],
                         "params": layer.get_weights()[0], "bias": layer.get_weights()[1]}

        except:
            dic_layer = {"name": layer.name, "in": int(layer.input.shape[-1]), "neurons": 0,
                         "out": int(layer.output.shape[-1]), "activation": None,
                         "params": 0, "bias": 0}

        lst_layers.append(dic_layer)
    return lst_layers


def visualize_nn(model, description=False, figsize=(10, 8)):
    lst_layers = utils_nn_config(model)
    layer_sizes = [layer["out"] for layer in lst_layers]

    fig = plt.figure(figsize=figsize)
    ax = fig.gca()
    ax.set(title=model.name)
    ax.axis('off')
    left, right, bottom, top = 0.1, 0.9, 0.1, 0.9
    x_space = (right - left) / float(len(layer_sizes) - 1)
    y_space = (top - bottom) / float(max(layer_sizes))
    p = 0.025

    for i, n in enumerate(layer_sizes):
        top_on_layer = y_space * (n - 1) / 2.0 + (top + bottom) / 2.0
        layer = lst_layers[i]
        color = "green" if i in [0, len(layer_sizes) - 1] else "blue"
        color = "red" if (layer['neurons'] == 0) and (i > 0) else color

        # descriptions
        if description is True:
            d = i if i == 0 else i - 0.5
            if layer['activation'] is None:
                plt.text(x=left + d * x_space, y=top, fontsize=10, color=color, s=layer["name"].upper())
            else:
                plt.text(x=left + d * x_space, y=top, fontsize=10, color=color, s=layer["name"].upper())
                plt.text(x=left + d * x_space, y=top - p, fontsize=10, color=color, s=layer['activation'] + " (")
                plt.text(x=left + d * x_space, y=top - 2 * p, fontsize=10, color=color,
                         s="Σ" + str(layer['in']) + "[X*w]+b")
                out = " Y" if i == len(layer_sizes) - 1 else " out"
                plt.text(x=left + d * x_space, y=top - 3 * p, fontsize=10, color=color,
                         s=") = " + str(layer['neurons']) + out)

        # circles
        for m in range(n):
            color = "limegreen" if color == "green" else color
            circle = plt.Circle(xy=(left + i * x_space, top_on_layer - m * y_space - 4 * p), radius=y_space / 4.0,
                                color=color, ec='k', zorder=4)
            ax.add_artist(circle)

            # add text
            if i == 0:
                plt.text(x=left - 4 * p, y=top_on_layer - m * y_space - 4 * p, fontsize=10,
                         s=r'$X_{' + str(m + 1) + '}$')
            elif i == len(layer_sizes) - 1:
                plt.text(x=right + 4 * p, y=top_on_layer - m * y_space - 4 * p, fontsize=10,
                         s=r'$y_{' + str(m + 1) + '}$')
            else:
                plt.text(x=left + i * x_space + p,
                         y=top_on_layer - m * y_space + (y_space / 8. + 0.01 * y_space) - 4 * p, fontsize=10,
                         s=r'$H_{' + str(m + 1) + '}$')

    # links
    for i, (n_a, n_b) in enumerate(zip(layer_sizes[:-1], layer_sizes[1:])):
        layer = lst_layers[i + 1]
        color = "green" if i == len(layer_sizes) - 2 else "blue"
        color = "red" if layer['neurons'] == 0 else color
        layer_top_a = y_space * (n_a - 1) / 2. + (top + bottom) / 2. - 4 * p
        layer_top_b = y_space * (n_b - 1) / 2. + (top + bottom) / 2. - 4 * p
        for m in range(n_a):
            for o in range(n_b):
                line = plt.Line2D([i * x_space + left, (i + 1) * x_space + left],
                                  [layer_top_a - m * y_space, layer_top_b - o * y_space],
                                  c=color, alpha=0.5)
                if layer['activation'] is None:
                    if o == m:
                        ax.add_artist(line)
                else:
                    ax.add_artist(line)
    plt.show()
