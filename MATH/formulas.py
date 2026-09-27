def robot_count(k_PeLo, k_load, k_res,
                dataset, TTC):

    peak_req = dataset["OperationsInDay"] / dataset["WorkTimeInDay"] * k_PeLo
    k_avail = TTC["WorkTime"] / (TTC["WorkTime"] + TTC["ChargeTime"])
    Ef_perf = TTC["PassportPerformance"] * k_avail * k_load
    robot_count = (peak_req / Ef_perf) * k_res

    return {
        "ok": True, "robot_count": robot_count, "k_res": k_res, "k_PeLo": k_PeLo, "k_load": k_load,
        "peak_req": peak_req, "k_avail": k_avail, "Ef_perf": Ef_perf
    }

def CAPEX(k_solCost, k_res, k_PO, TTC,
          k_integ, k_PNR, k_learn, robot_count):

    equip = robot_count * k_solCost * TTC["Cost"]
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
        "ok": True, "opex" : opex, "service":service, "license":license, "electricity" :electricity,
        "conneciton":conneciton, "consumables": consumables, "repair": repair, "staff":staff
    }