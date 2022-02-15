from scipy.signal import find_peaks

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


def refl_fit(data,freq_data,window,delay_arr,filepath):
    save_dir = str(filepath) + '/delay_refl_fit/'
    f_guess = freq_data[dips]
    chi = np.empty((0,3))
    p(save_dir).mkdir(parents=True, exist_ok=True)

    try:
        for idx,val in enumerate(window):
            minpos = find_nearest_pos(freq_data,f_guess-val/2)
            maxpos = find_nearest_pos(freq_data,f_guess+val/2)
            f_data = freq_data[minpos:maxpos]
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
        print(f'Phi = {phi} doesnt work')
    arg_min = chi[:,1].argmin()
    best_window, _, delay_min = chi[arg_min]
    minpos = find_nearest_pos(freq,f_guess-best_window/2)
    maxpos = find_nearest_pos(freq,f_guess+best_window/2)
    f_data = freq_data[minpos:maxpos]
    phase_data = np.angle(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    mag_data = np.abs(data[:, 0] + 1j * data[:, 1])[minpos:maxpos]
    z_data = mag_data * np.exp(1j * phase_data)
    port1 = circuit.reflection_port(f_data, z_data)
    port1.autofit(electric_delay=delay_min,fr_guess=f_guess)
    powerbeta = power_beta(20*np.log10(mag_data).min(),20*np.log10(mag_data).max())

    fit_dict = {}
    for key,value in port1.fitresults.items():
        fit_dict[key] = value
        fit_dict['beta'] = port1.fitresults['Qi']/port1.fitresults['Qc']
        fit_dict['powerbeta'] = powerbeta
    port1.plotall()

    return fit_dict

    # df = pd.DataFrame([fit_dict]) #write results to dict so we can export to csv
    # if phi==0:
    #     f = open(save_dir + 'refl_params.csv','w')
    #     f.close()
    # with open(save_dir + 'refl_params.csv','a') as f:
    #     df.to_csv(f, mode='a', header=f.tell()==0)
    # port1.plotallsave_delay(save_dir + 'phi = ' + str(phi_val)+'.pdf')
    # warnings.filterwarnings("ignore")