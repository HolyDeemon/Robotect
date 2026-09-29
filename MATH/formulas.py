from MATH.Simulation import Simulation


def robot_count(k_PeLo, k_load, k_res,
                dataset, work_time, charge_time, efficiency):

    peak_req = dataset["OperationsInDay"] / dataset["WorkTimeInDay"] * k_PeLo
    k_avail = work_time / (work_time + charge_time)
    Ef_perf = efficiency * k_avail * k_load
    robot_count = (peak_req / Ef_perf) * k_res

    return {
        "ok": True, "robot_count": robot_count, "k_res": k_res, "k_PeLo": k_PeLo, "k_load": k_load,
        "peak_req": peak_req, "k_avail": k_avail, "Ef_perf": Ef_perf
    }

def CAPEX(k_solCost, k_res, k_PO, cost,
          k_integ, k_PNR, k_learn, robot_count):

    equip = robot_count * k_solCost * cost
    PO = equip * k_PO
    integration = equip * k_integ
    comm = equip * k_PNR
    learn = equip * k_learn
    reserve = (equip + PO + integration + comm + learn) * k_res

    capex = equip + PO + integration + comm + learn + reserve

    return {
        "ok": True, "CAPEX": capex, "equip": equip, "PO": PO,
        "integration": integration, "comm": comm, "learn": learn, "reserve": reserve,
        "k_res": k_res, "k_PO": k_PO, "k_integ": k_integ, "k_PNR": k_PNR, "k_learn": k_learn, "robot_count": robot_count
    }

def OPEX(k_service, k_lic, k_conn, k_cons, k_rep, k_FOT, salary,
         capex, equip, count, power_kW, work_hours, tariff):
    service = equip * k_service
    license = equip * k_lic
    electricity = count * power_kW * work_hours * tariff
    conneciton = equip * k_conn
    consumables = equip * k_cons
    repair = capex * k_rep
    staff = count * salary * 12 * k_FOT

    opex = service + license + electricity + conneciton + consumables + repair + staff

    return {
        "ok": True, "OPEX" : opex, "service":service, "license":license, "electricity" :electricity,
        "conneciton":conneciton, "consumables": consumables, "repair": repair, "staff":staff
    }

def year_econ_effect(opex, shortened_count, salary, k_FOT, add_inc, prev_los):
    hum_OPEX = shortened_count * salary * 12 * k_FOT
    delta_OPEX = opex - hum_OPEX
    year_effect = -delta_OPEX + add_inc + prev_los
    return {"ok": True, "year_effect":year_effect, "hum_OPEX": hum_OPEX, "delta_OPEX": delta_OPEX}

def payback_period(capex, year_effect):
    payback_period = capex/year_effect
    return {"ok":True, "payback_period": payback_period}

def ROI(capex, year_effect, horizon):
    ROI = (year_effect * horizon / capex) * 100
    return {"ok":True, "ROI": ROI}

def TCO(capex, opex, horizon, equip, accum_life, inflation):
    battery_change = equip * 0.2 * (horizon / accum_life)
    OPEX_sum = 0
    for n in range(1, horizon + 1):
        OPEX_sum += opex * (1 + inflation) ** (n - 1)
    TCO = capex + battery_change + OPEX_sum
    return {"ok": True, "TCO": TCO, "OPEX_sum": OPEX_sum, "battery_change": battery_change}

def sim_k_avail(sim: Simulation):
    avg_charge_time = sum(r.charge_ticks for r in sim.robots)/len(sim.robots)
    return sim.clock.sim_hours / (sim.clock.sim_hours + avg_charge_time)

def sim_Ef_perf(sim: Simulation, k_avail, effectivness):
    return effectivness * sim.kpi()["utilization_pct"] * k_avail

def sim_N_robots(ef_perf, peak_load, k_res):
    return (peak_load / ef_perf) * k_res

def  sim_electricity(sim: Simulation, power, tariff):
    all_time = 0
    for i in range(len(sim.robots)):
        all_time += sim.robots[0].charge_ticks
    return all_time * power * tariff

def sim_year_effect(sim: Simulation, electricity):
    Add_inc = (sim.robot_spec.efficiency - 6) * sim.clock.sim_hours * 100
    return Add_inc - electricity