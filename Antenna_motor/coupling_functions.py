from scipy.signal import find_peaks
import numpy as np
from pathlib import Path as p
from resonator_tools import circuit
import warnings
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')


def dipfinder(data,freq,p_width, prom, Height):
    # Find peaks with data given as db
    dips = find_peaks(-data, prominence=prom, height=Height, width=p_width)
    f0 = freq[dips[0]]
    return dips[0], f0, dips

def find_nearest_pos(a, a0):
    "position in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return idx

def power_beta(on,off):
    return (1-np.sqrt(10**(on/10)/10**(off/10)))/(1+np.sqrt(10**(on/10)/10**(off/10)))


def refl_fit(data,freq,dips,window,delay_arr,filepath):
    warnings.filterwarnings("ignore")
    save_dir = filepath/'refl_fit'
    f_guess = freq[dips]
    chi = np.empty((0,3))
    p(save_dir).mkdir(parents=True, exist_ok=True)

    try:
        for idx,val in enumerate(window):
            minpos = find_nearest_pos(freq,f_guess-val/2)
            maxpos = find_nearest_pos(freq,f_guess+val/2)
            f_data = freq[minpos:maxpos]
            phase_data = np.angle(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
            mag_data = np.abs(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
            z_data = mag_data*np.exp(1j*phase_data)
            port1 = circuit.reflection_port(f_data, z_data)

            for i in delay_arr:
                port1.autofit(electric_delay=i,fr_guess=f_guess)
                if port1.fitresults.get('chi_square') is not None:
                    chi = np.vstack((chi,[val,port1.fitresults['chi_square'],i]))
                else:
                    chi = np.vstack((chi,[val,1,i]))
    except:
        print(f'Doesnt work')
    arg_min = chi[:,1].argmin()
    best_window, _, delay_min = chi[arg_min]
    minpos = find_nearest_pos(freq,f_guess-best_window/2)
    maxpos = find_nearest_pos(freq,f_guess+best_window/2)
    f_data = freq[minpos:maxpos]
    phase_data = np.angle(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    mag_data = np.abs(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    z_data = mag_data * np.exp(1j * phase_data)
    port1 = circuit.reflection_port(f_data, z_data)
    port1.autofit(electric_delay=delay_min)
    powerbeta = power_beta(20*np.log10(mag_data).min(),20*np.log10(mag_data).max())

    fit_dict = {}
    for key,value in port1.fitresults.items():
        fit_dict[key] = value
        fit_dict['beta'] = port1.fitresults['Qi']/port1.fitresults['Qc']
        fit_dict['powerbeta'] = powerbeta
    #port1.plotallsave_delay(save_dir/'test.pdf')
    port1.plotall_delay()
    return fit_dict

def test_refl_fit(data,freq,dips,initial_window,delay_arr,filepath):
    warnings.filterwarnings("ignore")
    save_dir = filepath/'refl_fit'
    f_guess = freq[dips]
    chi = np.empty((0,3))
    p(save_dir).mkdir(parents=True, exist_ok=True)

    minpos = find_nearest_pos(freq,f_guess-initial_window/2)
    maxpos = find_nearest_pos(freq,f_guess+initial_window/2)
    f_data = freq[minpos:maxpos]
    phase_data = np.angle(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    mag_data = np.abs(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    z_data = mag_data*np.exp(1j*phase_data)
    port1 = circuit.reflection_port(f_data, z_data)

    for i in delay_arr:
        port1.autofit(electric_delay=i)
        if port1.fitresults.get('chi_square') is not None:
            chi = np.vstack((chi,[port1.fitresults['Ql'],port1.fitresults['chi_square'],i]))
        else:
            chi = np.vstack((chi,[0,1,i]))

    arg_min = chi[:,1].argmin()
    Ql, _, delay_min = chi[arg_min]
    best_window = f_guess/Ql
    minpos = find_nearest_pos(freq,f_guess-best_window)
    maxpos = find_nearest_pos(freq,f_guess+best_window)
    f_data = freq[minpos:maxpos]
    phase_data = np.angle(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    mag_data = np.abs(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    z_data = mag_data * np.exp(1j * phase_data)
    port1 = circuit.reflection_port(f_data, z_data)
    port1.autofit(electric_delay=delay_min)
    powerbeta = power_beta(20*np.log10(mag_data).min(),20*np.log10(mag_data).max())

    fit_dict = {}
    for key,value in port1.fitresults.items():
        fit_dict[key] = value
        fit_dict['beta'] = port1.fitresults['Qi']/port1.fitresults['Qc']
        fit_dict['powerbeta'] = powerbeta
        fit_dict['best_window'] = best_window
    #port1.plotallsave_delay(save_dir/'test.pdf')
    port1.plotall_delay()
    return fit_dict

def plot_freq_vs_db_mag(freq_GHz,db_data,fcent):
    plt.ion()
    fig = plt.figure("VNA")
    plt.draw()
    fig.clf()
    move_figure()
    ax = fig.add_subplot(111)
    ax.set_title("f = %.3f GHz" % (fcent / 1e9), fontsize=16)
    ax.plot(freq_GHz, db_data, "g")
    #ax.scatter(freq_GHz,db_data[dips],marker='X',color='red',s=30)
    ax.set_ylabel(r'$S_{21}$ [dB]')
    ax.set_xlabel('Frequency [GHz]')
    plt.axis('tight')
    plt.pause(0.1)

    # df = pd.DataFrame([fit_dict]) #write results to dict so we can export to csv
    # if phi==0:
    #     f = open(save_dir + 'refl_params.csv','w')
    #     f.close()
    # with open(save_dir + 'refl_params.csv','a') as f:
    #     df.to_csv(f, mode='a', header=f.tell()==0)
    # port1.plotallsave_delay(save_dir + 'phi = ' + str(phi_val)+'.pdf')

def plot_freq_vs_db_mag_vs_phase(freq_GHz,db_data,phase,fcent):
    plt.ion()
    fig = plt.figure("VNA")
    plt.draw()
    fig.clf()
    move_figure()
    ax = fig.add_subplot(111)
    ax2 = ax.twinx()
    ax.set_title("f = %.3f GHz" % (fcent / 1e9), fontsize=16)
    ax.plot(freq_GHz, db_data, "g")
    ax2.plot(freq_GHz,phase,'b')
    ax2.set_ylabel('Phase (deg)')
    #ax.scatter(freq_GHz,db_data[dips],marker='X',color='red',s=30)
    ax.set_ylabel(r'$S_{21}$ [dB]')
    ax.set_xlabel('Frequency [GHz]')
    plt.tight_layout()
    plt.pause(0.1)

def move_figure(position="top-left"):
    '''
    Move and resize a window to a set of standard positions on the screen.
    Possible positions are:
    top, bottom, left, right, top-left, top-right, bottom-left, bottom-right
    '''

    mgr = plt.get_current_fig_manager()
    #gr.full_screen_toggle()  # primitive but works to get screen size
    py = mgr.canvas.height()
    px = mgr.canvas.width()

    d = 20  # width of the window border in pixels
    if position == "top":
        # x-top-left-corner, y-top-left-corner, x-width, y-width (in pixels)
        mgr.window.setGeometry(d, 4*d, px - 2*d, py/2 - 4*d)
    elif position == "bottom":
        mgr.window.setGeometry(d, py/2 + 5*d, px - 2*d, py/2 - 4*d)
    elif position == "left":
        mgr.window.setGeometry(d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "right":
        mgr.window.setGeometry(px/2 + d, 4*d, px/2 - 2*d, py - 4*d)
    elif position == "top-left":
        mgr.window.setGeometry(d, 4*d,600,500)
    elif position == "top-right":
        mgr.window.setGeometry(px/2 + d, 4*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "bottom-left":
        mgr.window.setGeometry(d, py/2 + 5*d, px/2 - 2*d, py/2 - 4*d)
    elif position == "bottom-right":
        mgr.window.setGeometry(px/2 + d, py/2 + 5*d, px/2 - 2*d, py/2 - 4*d)
