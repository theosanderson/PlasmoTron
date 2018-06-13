def create_container_instance(name, grid, spacing, diameter, depth,
                              volume=0, slot=None, label=None, Transposed=False):
    from opentrons import robot
    from opentrons.containers.placeable import Container, Well
    
    if slot is None:
        raise RuntimeError('"slot" argument is required.')
    if label is None:
        label = name
    columns, rows = grid
    col_spacing, row_spacing = spacing
    custom_container = Container()
    well_properties = {
        'type': 'custom',
        'diameter': diameter,
        'height': depth,
        'total-liquid-volume': volume
    }
   
    for r in range(rows):
            for c in range(columns):
                well = Well(properties=well_properties)
                well_name = chr(c + ord('A')) + str(1 + r)
                if Transposed:
                    coordinates = (r * col_spacing, c * row_spacing, 0)
                else:
                    coordinates = (c * col_spacing, r * row_spacing, 0)
                custom_container.add(well, well_name, coordinates)
   

    # if a container is added to Deck AFTER a Pipette, the Pipette's
    # Calibrator must update to include all children of Deck
    for _, instr in robot.get_instruments():
        if hasattr(instr, 'update_calibrator'):
            instr.update_calibrator()
            
    custom_container.properties['type'] = name
    custom_container.get_name = lambda: label

    # add to robot deck
    robot.deck[slot].add(custom_container, label)

    return custom_container