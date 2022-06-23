import core.models as models

def update_metrics(seat: models.Seat):
    # keep it simple: store metrics as a dict of lists before commiting to db
    ELIGIBILITY = 0
    VALUE = 1
    Type = models.BinarySeatMetric.Metric
    metrics = {}
    for m in Type.values:
        metrics[m] = [False, False]
    # access as metrics[METRIC][ELIGIBILITY/VALUE]

    # calculate binary metrics by iterating over actions
    actions = seat.allActionsInHand()
    actions = actions.filter(round=models.Action.Round.PREFLOP) # preflop only for now
    seat_actions = actions.filter(seat=seat) # this seat's pre-flop
    
    # this seat's first pre-flop action
    first_action = seat_actions.order_by('number').first()

    # first action will be None if not found
    # if there's no first action, action must have folded to the player in the big blind
    # no metrics are eligible
    if first_action:
        metrics[Type.VPIP][ELIGIBILITY] = True
        metrics[Type.PREFLOP_RAISE][ELIGIBILITY] = True # edge case: BB > stack
        metrics[Type.PREFLOP_ALLIN][ELIGIBILITY] = True
                
        # determine eligibility for a 3-bet, was there a raise before?
        actions_prior = actions.filter(number__lt=first_action.number)
        metrics[Type.PREFLOP_3BET][ELIGIBILITY] = actions_prior.filter(type=models.Action.Type.RAISE).count() > 0

        if first_action.type == models.Action.Type.CALL:
            metrics[Type.VPIP][VALUE] = True
        elif first_action.type == models.Action.Type.RAISE:
            metrics[Type.VPIP][VALUE] = True
            metrics[Type.PREFLOP_RAISE][VALUE] = True
            if metrics[Type.PREFLOP_3BET][ELIGIBILITY]:
                metrics[Type.PREFLOP_3BET][VALUE] = True
    
    # commit metrics to database
    for (k,v) in metrics.items():
        models.BinarySeatMetric.objects.update_or_create(
            seat=seat, type=k,
            eligibility=v[ELIGIBILITY], value=v[VALUE]
        )

    # record update   
    seat.metrics_fresh = True
    seat.save()
    