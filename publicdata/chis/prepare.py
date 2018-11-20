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

def extract_categories(fspath):
    """
    Create a Metatab doc with the schema for a CHIS file, including the categorical values.

    :param fspath: Path to the stata file.
    :return:
    """

    dfs = pd.read_stata(fspath)
    itr = pd.read_stata(fspath, iterator=True)

    var_d = itr.variable_labels()

    # We ought to be able to just use the value_labels() method to get value labels, but
    # there are a lot of variables it doesn't return values for. For those, we'll use
    # make_cat_map, which analyzes the categorical values directly.

    val_d = {} #itr.value_labels() # Actually it looks like value_labels is often wrong

    doc = mp.MetapackDoc()
    doc['Root'].get_or_new_term('Root.Title', 'Schema and Value Categories')
    doc['Root'].get_or_new_term('Root.Source', fspath)
    sch = doc.new_section('Schema', ['Description', 'Ordered'])
    tab = sch.new_term('Root.Table', 'adults')

    for col_name in dfs.columns:
        col = tab.new_child('Column', col_name, description=var_d[col_name])

        try:
            val_map = val_d[col_name]
        except KeyError:
            try:
                val_map = make_cat_map(dfs, col_name)
            except AttributeError:
                # Probably, column is not a category
                val_map = {}

        try:
            if dfs[col_name].cat.ordered:
                col.new_child('Column.Ordered', 'true')
        except AttributeError as e:
            pass

        for k, v in val_map.items():
            col.new_child('Column.Value', k, description=v)

    doc.cleanse() # Creates Modified and Identifier

    return doc


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