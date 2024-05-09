#!/bin/python3

import sys
import math
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from mplcairo import operator_t # mpl backend for additive blending support

#set mplcairo as mpl backend
mpl.use("module://mplcairo.qt")



def main():
    #read from the path specified in the first command line arg
    if len(sys.argv) > 1:
        input_file = open(sys.argv[1], 'r')
    else:
        print("usage: %s INPUT_FILE" % sys.argv[0])
        exit(1)

    
    signals = get_signals_data(input_file)
    
    interpolate_x_values(signals)

    print_signals_info(signals)

    line_mode=(len(sys.argv) > 2 and sys.argv[2] == "line")
    plot_signals(signals, line_mode)

# get next line, ignoring comments (with # syntax) and empty lines. returns None on EOF
def input_next_line(fp):
    while True:
        s = fp.readline()
        if s == '':
            return None # EOF reached
        s = s.split('#')[0].strip()
        if len(s):
            return s

def get_signal_len(fp):
    old_pos = fp.tell()
    ret = 0
    while True:
        l = input_next_line(fp)
        if l == "END_OF_SIGNAL":
            fp.seek(old_pos)
            return ret
        ret += 1

# from a string containing whitespace-separated numbers return an array of floats. * in the string will correspond to a None value in the array
def str_to_array_of_optional_floats(s):
    ret = []
    for word in s.split():
        if word == "*":
            ret.append(float('nan'))
        else:
            ret.append(float(word))
    return ret


# read the input file, returns an dictionary of signals, where each signal is a tuple of two parallel arrays with its label as key {label : (x_array, y_array), ...}
def get_signals_data(fp):
    signals = {}

    # get each signal's data
    while True:
        # get signal label
        label = input_next_line(fp)
        if label == None:
            break # EOF

        signal_len = get_signal_len(fp)
        x = np.empty(signal_len)
        y = np.empty(signal_len)

        # get samples
        for i in range(signal_len):
            line = input_next_line(fp)
            if line == "END_OF_SIGNAL":
                break
            sample = str_to_array_of_optional_floats(line)
            x[i] = sample[0]
            y[i] = sample[1]
        else:
            assert(input_next_line(fp) == "END_OF_SIGNAL")

        signals[label] = (x,y)
    return signals


# interpolate missing x-coord values
def interpolate_x_values(signals):
    for label in signals:
        x,_ = signals[label]
        for i in range(len(x)):
            if math.isnan(x[i]):
                #make a dictionary with the contents of x
                x_dict = { i:v for i,v in enumerate(x) if not math.isnan(v) }
        
                x[i] = np.interp(i, [*x_dict.keys()], [*x_dict.values()])

# print signal information: how many datapoints, deltax from beginning to end, sample frequency
def print_signals_info(signals):
    print("signals:")
    for label,(x,y) in signals.items():
        deltax = max(x) - min(x)
        print("> %s: %d datapoints / %f delta x = %f" % (label, len(y), deltax, len(y)/deltax))

# plot the signals with matplotlib
def plot_signals(signals, line_mode):
    # supposedly increases performance
    mpl.style.use("fast")
    mpl.rcParams['path.simplify_threshold'] = 1.0


    fig, ax = plt.subplots()
    # The figure and axes background must be made transparent to use additive blending
    fig.patch.set(alpha=0, color="#000000")
    ax.patch.set(alpha=0, color="#000000")
    
    color_palette = ['#ff0000', '#0000ff', '#00ff00', 'c', 'm', 'y', 'k']

    for i, (label, (x,y)) in enumerate(signals.items()):
        color = color_palette[i % len(color_palette)]

        if line_mode:
            ax.plot(x,y,c=color,label=label,marker='.')
        else:
            pc = ax.scatter(x, y, c=color, label=label, marker='.')
            operator_t.ADD.patch_artist(pc)  # Use additive blending.
        
    plt.legend(loc="upper left")
    plt.show()

main()
