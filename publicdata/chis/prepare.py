# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

"""
Functions for preparing a chis dataset

"""

import pandas as pd
import metapack as mp

def make_cat_map(df, column):
    """Extract the mapping between category names and codes from the dataset. There should be an interface
    on the categorical index type for this map, but I could not find it. """

    t = pd.DataFrame( {'codes': df[column].cat.codes, 'values': df[column]} ).drop_duplicates().sort_values('codes')
    return { e.codes:e.values for e in list(t.itertuples())}


def convert_to_numbers(df):
    """Convert all of the categorical values that are entirely numbers to floats. """

    df = df.copy()

    for col_name in df.columns:
        try:
            cats = list(df[col_name].cat.categories)
            [float(e) for e in cats]
            df[col_name] = df[col_name].astype(float)

        except ValueError:
            # Categories, but they are not numbers
            pass

        except AttributeError:
            # not a categorical
            pass

    return df


def table_category_map(doc, table_name):
    """Given the schema document created by extract_categories, return a dict categories for a given table

    Normally, the ``doc`` parameter is loaded form a Metapack reference. For instance, if  the doc from
    extract_categories was written to 'schema.csv' oin the root of the package, the metadata.csv metadata
    file may have:

      Section: References
      Reference:	metatab+file:schema.csv	adult_2017_categories
      Reference.name: adult_2017_categories

    Then, in code ( for instance a Jupyter notebook ) :

        sch = pkg.reference('adult_2017_categories').resolved_url.doc
        cat_map = table_category_map(sch, 'adults')

        df = pkg.resource('adult_2017').dataframe()

        df_cat = to_categories(df, cat_map)


    :param doc: Metatab document created by extract_categories
    :param table_name: Name of a table in the doc
    :return:
    """
    table = doc.find_first('Root.Table', table_name)

    if not table:
        return {}

    value_map = {}

    for column in table.find('Column'):

        value_map[column.value] = {}

        if column.props.get('ordered'):
            #print("HERE!")
            value_map[column.value]['@ordered'] = True
        else:
            pass
            #print(column.children)

        for v in column.find('Value'):
            value_map[column.value][int(v.value)] = v.description

    return value_map

def to_codes(df):
    """Return a dataframe with all of the categoricals represented as codes"""
    df = df.copy()
    cat_cols = df.select_dtypes(['category']).columns
    df[cat_cols] = df[cat_cols].apply(lambda x: x.cat.codes)
    return df

def to_categories(df, cat_map):
    """ Convert a dataframe to use categories, based on the category map created by table_category_map.

    :param df:  CHIS Dataframe to convert, loaded from Metatab
    :param cat_map:  category map, from table_category_map
    :return:
    """

    df = df.copy()

    for col in df.columns:

        def try_number(v):

            if v == 'nan':  # ername_categories() don't like real nan or None
                return v

            try:
                return int(v)
            except ValueError:
                pass

            try:
                return float(v)
            except ValueError:
                pass

            return v

        ordered = True if cat_map[col].get('@ordered') else False
        cm = {k: try_number(v) for k, v in cat_map[col].items() if k != '@ordered' and v != 'nan'}

        try:
            df[col] = df[col].astype(pd.api.types.CategoricalDtype(ordered=ordered))
            df[col].cat.rename_categories(cm, inplace=True)
        except KeyError:
            pass
        except ValueError:
            raise

    return df