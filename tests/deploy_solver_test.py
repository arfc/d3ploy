import random 

def deploy_solver(commod, diff):
    """ This function optimizes prototypes to deploy to minimize over
        deployment of prorotypes.

    Paramters:
    ----------
    commod: str
        commodity to deploy the prototypes for
    diff: float
        lack in supply
    
    Returns:
    --------
    deploy_dict: dict
        key: prototype name
        value: # to deploy
    """
    proto_commod = commod
    min_cap = min(commod.values())
    if diff < min_cap:
        return {}
    
    key_list = get_asc_key_list(commod)

    after = diff
    deploy_dict = {}
    for proto in key_list:
        # if diff still smaller than the proto capacity,
        if after > proto_commod[proto]:
            # get one
            deploy_dict[proto] = 1
            # see what the diff is now
            after -= proto_commod[proto]
            # if this is not enough, keep deploying until it's smaller than its cap
            while after > proto_commod[proto]:
                deploy_dict[proto] += 1
                after -= proto_commod[proto]
    return deploy_dict


def get_asc_key_list(dicti):
    key_list = [' '] * len(dicti.values())
    sorted_caps = sorted(dicti.values())
    for key, val in dicti.items():
        indx = sorted_caps.index(val)
        key_list[indx] = key
    return key_list


for i in range(100):
    print('TRIAL ', i)
    diff = random.uniform(0.1, 30.0)
    commod = {}
    for i in range(4):
        commod.update({str(i): random.uniform(0.1, 9.9)})

    deploy_dict = deploy_solver(commod, diff)

    # actually deploy and see if it's good
    final_diff = diff
    for key, val in deploy_dict.items():
        final_diff -= val * commod[key]
    
    if final_diff > min(commod.values()):
        print('YA FAIL')
        print(final_diff)
        print(commod)
        raise ValueError('The difference after deployment exceeds the capacity of the smallest deployable prototype')
    else:
        print('GOOD JOB')
        print(final_diff)
        print(commod)
