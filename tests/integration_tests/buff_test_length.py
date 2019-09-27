{
    "simulation": {
        "archetypes": {
            "spec": [
                {"lib": "agents", "name": "NullRegion"},
                {"lib": "cycamore", "name": "Source"},
                {"lib": "cycamore", "name": "Reactor"},
                {"lib": "cycamore", "name": "Sink"},
                {"lib": "d3ploy.demand_driven_deployment_inst",
                 "name": "DemandDrivenDeploymentInst"},
                {"lib": "d3ploy.supply_driven_deployment_inst",
                 "name": "SupplyDrivenDeploymentInst"}
            ]
        },
        "control": {"duration": "10", "startmonth": "1", "startyear": "2000"},
        "facility": [
            {
                "config": {"Source": {"outcommod": "fuel",
                                      "outrecipe": "fresh_uox",
                                                   "throughput": "1"}},
                "name": "source"
            },
            {
                "config": {"Sink": {"in_commods": {"val": "spent_uox"},
                                    "max_inv_size": "10"}},
                "name": "sink"
            },
            {
                "config": {
                    "Reactor": {
                        "assem_size": "1",
                        "cycle_time": "1",
                        "fuel_incommods": {"val": "fuel"},
                        "fuel_inrecipes": {"val": "fresh_uox"},
                        "fuel_outcommods": {"val": "spent_uox"},
                        "fuel_outrecipes": {"val": "spent_uox"},
                        "n_assem_batch": "1",
                        "n_assem_core": "1",
                        "power_cap": "1",
                        "refuel_time": "0"
                    }
                },
                "name": "reactor1"
            }
        ],
        "recipe": [
            {
                "basis": "mass",
                "name": "fresh_uox",
                "nuclide": [{"comp": "0.711", "id": "U235"},
                            {"comp": "99.289", "id": "U238"}]
            },
            {
                "basis": "mass",
                "name": "spent_uox",
                "nuclide": [{"comp": "50", "id": "Kr85"},
                            {"comp": "50", "id": "Cs137"}]
            }
        ]
    }
}
