import Calculator_RenalTransplant as cal
import numpy as np
import pandas as pd


#### audit report template- calculator name, date calculated, date of audit, calulation number, live results, audit results, comment

#function to create the audit report
def validation(numeric_results_df):
    return calculate_score(validate_bmi(numeric_results_df))

#function to add comments to the dataset
def add_comment(existing_comment,additional_comment):
    if(existing_comment!=' '):
       return existing_comment+' and '+additional_comment
    else:
        return additional_comment

#function to validate the bmi calculations
def validate_bmi(numeric_results_df):
    bmi_series = cal.calc_bmi(height=numeric_results_df['Height'], weight=numeric_results_df['Weight'])
    #finding the incorrect bmi calculations
    validation_report=numeric_results_df.copy()
    validation_report['comments']=' '
    # validation_report.loc['comments']= validation_report['comments'].apply(lambda x: add_comment(x,'incorrect bmi calculation'))
    validation_report.loc[validation_report[bmi_series - validation_report['bmis'] > 0],'comments']=\
        validation_report[validation_report[bmi_series - validation_report['bmis'] > 0]].comments.apply(lambda x: add_comment(x,'incorrect bmi calculation'))

    # bmi_series[bmi_series - numeric_results_df['bmis'] > 0]
    #finding out of bound bmi calculations
    validation_report.loc[validation_report['bmis'] > 200, 'comments'] = validation_report[
        validation_report['bmis'] > 200].comments.apply(lambda x: add_comment(x, 'bmi out of bounds'))
    #finding incorrect height entered
    validation_report.loc[validation_report['Height'] < 10, 'comments'] = validation_report[
        validation_report['Height'] < 10].comments.apply(
        lambda x: add_comment(x, 'possible wrong height entered'))

    validation_report['test_bmi']=bmi_series

    return validation_report

def calculate_score(numeric_results_df):
    bmi_series = cal.calc_bmi(height=numeric_results_df['Height'], weight=numeric_results_df['Weight'])
    # numeric_results_df[['COPD','Nonambulatory','CHF','Insulin','CAD','PVD','CVD','HT','SmokerCurrent','Employed']]
    history_list = ['COPD', 'Nonambulatory', 'CHF', 'Insulin', 'CAD', 'PVD', 'CVD', 'HT', 'SmokerCurrent', 'Employed']
    months_to_accepted = (numeric_results_df['dateAccepted'] - numeric_results_df['dateFirstRRT']) / np.timedelta64(1,
                                                                                                                    'M')
    months_to_referal = (numeric_results_df['dateReferredtoTxCtr'] - numeric_results_df[
        'dateFirstRRT']) / np.timedelta64(1, 'M')

    # merge the two datasets and if both exist, select months_to_accepted
    months_to_listing = months_to_accepted.combine_first(months_to_referal)

    scored_df = pd.DataFrame()
    scored_df['Albumin'] = numeric_results_df['Albumin'].apply(cal.score_albumin)
    scored_df['bmis'] = bmi_series.apply(cal.score_bmi)
    scored_df['Cause'] = numeric_results_df['Cause'].apply(cal.score_cause)
    for history in history_list:
        scored_df[history] = numeric_results_df[history].apply(cal.score_history, args=(history,))

    scored_df['Age'] = numeric_results_df['Age'].apply(cal.score_age)
    scored_df['EthnicGroup'] = numeric_results_df['EthnicGroup'].apply(cal.score_ethnicity)
    scored_df['yearFirstRRT'] = numeric_results_df['dateFirstRRT'].dt.year.apply(cal.score_first_rrt)
    scored_df['timeFromFirstRTT'] = months_to_listing.apply(cal.score_timefrom_frtt)
    scored_df['transplantation'] = -26

    scored_df['test_Survival_Factor'] = scored_df.sum(axis=1)
    scored_df['calc_Survival_Factor'] = numeric_results_df['Survival_Factor']
    scored_df['diff_Survival_Factor'] = scored_df['test_Survival_Factor'] - scored_df['calc_Survival_Factor']

    numeric_results_df['test_Survival_Factor'] = scored_df['test_Survival_Factor']
    numeric_results_df['diff_Survival_Factor'] = scored_df['diff_Survival_Factor']

    return validate_score(numeric_results_df,scored_df)

#function to validate the score
def validate_score(numeric_results_df,scored_df):
    # validation_report=numeric_results_df.copy()
    # add comments to paitents with incorrect calculations
    numeric_results_df.loc[numeric_results_df['test_Survival_Factor'] - numeric_results_df['Survival_Factor'] != 0,
                       'comments']=numeric_results_df[numeric_results_df['test_Survival_Factor'] - numeric_results_df['Survival_Factor'] != 0].\
        comments.apply(lambda x: add_comment(x,'These patients have incorrect calculations'))

    # numeric_results_df[scored_df['test_Survival_Factor'] - scored_df['calc_Survival_Factor'] != 0].to_csv(
    #     'test_failed.csv')

    #Check what patients had an uderestimate of survival
    numeric_results_df.loc[numeric_results_df['test_Survival_Factor'] - numeric_results_df['Survival_Factor'] < 0,
                       'comments'] = numeric_results_df[numeric_results_df['test_Survival_Factor'] - numeric_results_df['Survival_Factor'] < 0]. \
        comments.apply(lambda x: add_comment(x, 'These patients have underestimate of survival'))
    # numeric_results_df[scored_df['test_Survival_Factor'] - scored_df['calc_Survival_Factor'] < 0]
    # numeric_results_df[scored_df['test_Survival_Factor'] - scored_df['calc_Survival_Factor'] < 0].to_csv(
    #     'underestimate_survival.csv')

    #check what columns have null values
    numeric_results_df.loc[scored_df.isnull().any(axis=1),'comments']=\
        numeric_results_df[scored_df.isnull().any(axis=1)].comments.apply(lambda x: add_comment(x,'missing value'))
    # numeric_results_df[scored_df.isnull().any(axis=1)].to_csv('missing_value.csv')
    numeric_results_df.loc[scored_df['Cause'].isnull(), 'comments'] = \
        numeric_results_df[scored_df['Cause'].isnull()].comments.apply(lambda x: add_comment(x, 'missing cause'))
    # numeric_results_df[scored_df['Cause'].isnull()].to_csv('missing_cause.csv')
    numeric_results_df.loc[scored_df['Employed'].isnull(), 'comments'] = \
        numeric_results_df[scored_df['Employed'].isnull()].comments.apply(lambda x: add_comment(x, 'missing employed'))
    # numeric_results_df[scored_df['Employed'].isnull()].to_csv('missing_employed.csv')
    numeric_results_df.loc[scored_df['HT'].isnull(), 'comments'] = \
        numeric_results_df[scored_df['HT'].isnull()].comments.apply(lambda x: add_comment(x, 'missing ht'))
    # numeric_results_df[scored_df['HT'].isnull()].to_csv('missing_ht.csv')
    numeric_results_df.loc[scored_df['bmis'].isnull(), 'comments'] = \
        numeric_results_df[scored_df['bmis'].isnull()].comments.apply(lambda x: add_comment(x, 'missing bmis'))
    # numeric_results_df[scored_df['bmis'].isnull()].to_csv('missing_bmi.csv')

    return numeric_results_df

