__author__ = 'Deepali Rajawat'


def gradient(bdesired, bmeasured):
    grad = -2 * (bdesired - bmeasured)  # make sure this returns as float
    return grad


def cost(bdesired, bmeasured):
    costfunc = (bdesired - bmeasured) ** 2
    return costfunc


def gradient_desc(startbeta, desiredbeta, learn_rate=0.001, n_iter=100, tolerance=1e-06):
    #need to change to motor
    step_size = int(gradient(desiredbeta, current_beta) * learn_rate)
    # if negative go up if positive go down? idk
    for i in range(n_iter):
        current_beta = current_beta - gradient(desiredbeta, current_beta) * learn_rate
