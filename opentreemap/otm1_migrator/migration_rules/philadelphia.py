from otm1_migrator.migration_rules.standard_otm1 import MIGRATION_RULES

UDFS = {
    'plot': {
        'owner_additional_id': {
            'udf.name': 'Owner Additional Id'
        },
        'owner_additional_properties': {
            'udf.name': 'Owner Additional Properties'
        },
        'type': {
            'udf.name': 'Plot Type',
            'udf.choices': ['Well/Pit', 'Median/Island', 'Tree Lawn',
                            'Park', 'Planter', 'Other', 'Yard',
                            'Natural Area']
        },
        'powerline_conflict_potential': {
            'udf.name': 'Powerlines Overhead',
            'udf.choices': ['Yes', 'No', 'Unknown']
        },
        'sidewalk_damage': {
            'udf.name': 'Sidewalk Damage',
            'udf.choices': ['Minor or No Damage', 'Raised More Than 3/4 Inch']
        }
    },
    'tree': {
        'sponsor': {'udf.name': 'Sponsor'},
        'projects': {'udf.name': 'Projects'},
        'canopy_condition': {
            'udf.name': 'Canopy Condition',
            'udf.choices': ['Full - No Gaps',
                            'Small Gaps (up to 25% missing)',
                            'Moderate Gaps (up to 50% missing)',
                            'Large Gaps (up to 75% missing)',
                            'Little or None (up to 100% missing)']
        },
        'condition': {
            'udf.name': 'Tree Condition',
            'udf.choices': ['Dead', 'Critical', 'Poor',
                            'Fair', 'Good',
                            'Very Good', 'Excellent']
        }
    }
}

SORT_ORDER_INDEX = {
    'Bucks': 3,
    'Burlington': 4,
    'Camden': 5,
    'Chester': 6,
    'Delaware': 7,
    'Gloucester': 8,
    'Kent': 9,
    'Mercer': 10,
    'Montgomery': 11,
    'New Castle': 12,
    'Salem': 13,
    'Sussex': 14,
}


def mutate_boundary(boundary_obj, boundary_dict):
    otm1_fields = boundary_dict.get('fields')
    if ((boundary_obj.name.find('County') != -1
         or boundary_obj.name == 'Philadelphia')):
        boundary_obj.category = 'County'
        boundary_obj.sort_order = 1
    elif otm1_fields['county'] == 'Philadelphia':
        boundary_obj.category = 'Philadelphia Neighborhood'
        boundary_obj.sort_order = 2
    else:
        county = otm1_fields['county']
        boundary_obj.category = county + ' Township'
        boundary_obj.sort_order = SORT_ORDER_INDEX[county]
    return boundary_obj

MIGRATION_RULES['boundary']['record_mutators'] = (MIGRATION_RULES['boundary']
                                                  .get('record_mutators', [])
                                                  + [mutate_boundary])
MIGRATION_RULES['species']['missing_fields'] |= {'other'}

# these fields don't exist in the ptm fixture, so can't be specified
# as a value that gets discarded. Remove them.
MIGRATION_RULES['species']['removed_fields'] -= {'family'}
MIGRATION_RULES['tree']['removed_fields'] -= {'pests', 'url'}

# this field doesn't exist, so can no longer have a to -> from def
del MIGRATION_RULES['species']['renamed_fields']['other_part_of_name']
