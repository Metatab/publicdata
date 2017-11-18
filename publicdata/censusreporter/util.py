


def melt(df):
    """Melt a census dataframe into two value columns, for the estimate and margin"""
    import pandas as pd

    # Intial melt
    melted = pd.melt(df, id_vars=list(df.columns[:9]), value_vars=list(df.columns[9:]))
    melted = melted[['gvid', 'variable', 'value']]

    # Make two seperate frames for estimates and margins.
    estimates = melted[~melted.variable.str.contains('_m90')].set_index(['gvid', 'variable'])
    margins = melted[melted.variable.str.contains('_m90')].copy()

    margins.columns = ['gvid', 'ovariable', 'm90']
    margins['variable'] = margins.ovariable.str.replace('_m90', '')

    # Join the estimates to the margins.
    final = estimates.join(margins.set_index(['gvid', 'variable']).drop('ovariable', 1))

    return final

# From http://stackoverflow.com/a/295466
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.type(
    """
    import re
    import unicodedata
    from six import text_type
    value = text_type(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf8')
    value = re.sub(r'[^\w\s-]', '-', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value


CACHE_NAME = 'pandasreporter'

def nl2br(v, is_xhtml= True ):
    if is_xhtml:
        return v.replace('\n','<br />\n')
    else :
        return v.replace('\n','<br>\n')