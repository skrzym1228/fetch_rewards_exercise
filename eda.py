
# data munging
import pandas as pd
import json
from flatten_json import flatten

# profiling
import missingno as msno
import matplotlib.pyplot as plt
from pandas_profiling import ProfileReport

# utility
from logzero import logger

#####################################################################
# Support Functions
#####################################################################
def convert_to_datetime(df, field_names):
    for fn in field_names:
        df[fn] = df[fn].apply(lambda x: pd.to_datetime(x, unit='ms'))


def analyze_and_save_df(df, name):
    csv_name = f'eda_results/{name}/{name}.csv'
    logger.debug(f'>>> saving {csv_name}')
    df.to_csv(csv_name,index=False)

    profile_output_name = f'eda_results/{name}/{name}_profile_output.html'
    logger.debug(f'>>> profiling {name}')
    df_profile = ProfileReport(df, correlations={"cramers": {"calculate": False}}, minimal=True, progress_bar=False)
    logger.debug(f'>>> saving profile as {profile_output_name}')
    df_profile.to_file(output_file=profile_output_name)

    missingno_output_name = f'eda_results/{name}/{name}_missingno_output.png'
    logger.debug(f'>>> analyzing missing data for {name}')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(100,50))
    msno.matrix(df, sparkline=False, ax=ax1)
    msno.bar(df, ax=ax2)
    msno.dendrogram(df, ax=ax3)
    msno.heatmap(df, ax=ax4)
    logger.debug(f'>>> saving plots to {missingno_output_name}')
    fig.savefig(missingno_output_name)
    plt.close(fig) 


#####################################################################
# Main Script
#####################################################################
# Read and Parse JSON files
#####################################################################
logger.info('')
logger.info('----START----- reading and parsing json files...')

logger.debug('> "receipts.json"')
with open('data/receipts.json', 'r') as f:
    receipts_parsed = [json.loads(line) for line in f]

logger.debug('> "brands.json"')
with open('data/brands.json', 'r') as f:
    brands_parsed = [json.loads(line) for line in f]

logger.debug('> "users.json"')
with open('data/users.json', 'r') as f:
    users_parsed = [json.loads(line) for line in f]

logger.info('---COMPLETE---')

#####################################################################
# Extraction
#####################################################################

logger.info('')
logger.info('----START----- extracting nested data...')
# Extract line_items from receipts data
logger.debug('> line items')
line_items_parsed = []
for r in receipts_parsed:
    receipt_id = r.get('_id').get('$oid')
    receipt_item_list = r.get('rewardsReceiptItemList', [])
    for ln in receipt_item_list:
        ln['receipt_id']=receipt_id
        line_items_parsed.append(ln)

# Extract bonus_point_reasons from receipts data
logger.debug('> bonus points earned reasons')
bonus_points_reasons_parsed = []
for r in receipts_parsed:
    receipt_id = r.get('_id').get('$oid')
    receipt_bp_reason_list = r.get('bonusPointsEarnedReason', '').split(', ')
    for reason in receipt_bp_reason_list:
        if len(reason) > 0:
            bonus_points_reasons_parsed.append({'receipt_id': receipt_id, 'bonus_points_earned_reason': reason})
logger.info('---COMPLETE---')

#####################################################################
# Transform, Analyze, and Save Final Tables
#####################################################################
logger.info('')
logger.info('----START----- transformation and analysis per final table...')

# Receipts DF
logger.debug('> receipts')
receipts_root_keys_to_ignore = {'rewardsReceiptItemList', 'bonusPointsEarnedReason'}
receipts_flattened = [flatten(d, root_keys_to_ignore=receipts_root_keys_to_ignore) for d in receipts_parsed]
receipts_df = pd.DataFrame(receipts_flattened)
receipts_field_names = [
    'receipt_id',
    'bonus_points_earned',
    'created_date',
    'scanned_date',
    'finished_date',
    'modified_date',
    'points_awarded_date',
    'points_earned',
    'purchased_date',
    'purchased_item_count',
    'rewards_receipt_status',
    'total_spent',
    'user_id'
]
receipts_df.columns = receipts_field_names
convert_to_datetime(receipts_df, ['created_date', 'scanned_date', 'finished_date', 'modified_date', 'points_awarded_date', 'purchased_date'])
#receipts_df.to_csv('receipts.csv',index=False)
analyze_and_save_df(receipts_df, 'receipts')


# Line Items DF
logger.debug('> line items')
line_items_flattened = [flatten(d) for d in line_items_parsed]
line_items_df = pd.DataFrame(line_items_flattened)
line_items_df['line_item_id'] = line_items_df['receipt_id'].astype(str) + line_items_df['partnerItemId'].astype(str)
line_items_field_names = [
    'barcode',
    'description',
    'final_price',
    'item_price',
    'needs_fetch_review',
    'partner_item_id',
    'prevent_target_gap_points',
    'quantity_purchased',
    'user_flagged_barcode',
    'user_flagged_new_item',
    'user_flagged_price',
    'user_flagged_quantity',
    'receipt_id',
    'needs_fetch_review_reason',
    'points_not_awarded_reason',
    'points_payer_id',
    'rewards_group',
    'rewards_product_partner_id',
    'user_flagged_description',
    'original_metabrite_barcode',
    'original_metabrite_description',
    'brand_code',
    'competitor_rewards_group',
    'discounted_item_price',
    'original_receipt_item_text',
    'item_number',
    'original_metabrite_quantity_purchased',
    'points_earned',
    'target_price',
    'competitive_product',
    'original_final_price',
    'original_metabrite_item_price',
    'deleted',
    'price_after_coupon',
    'metabrite_campaign_id',
    'line_item_id'
]
line_items_df.columns = line_items_field_names
analyze_and_save_df(line_items_df, 'line_items')

# Users DF
logger.debug('> users')
users_flattened = [flatten(d) for d in users_parsed]
users_df = pd.DataFrame(users_flattened)
# TODO: normalize field names
analyze_and_save_df(users_df, 'users')

# Brands DF
logger.debug('> brands')
brands_flattened = [flatten(d) for d in brands_parsed]
brands_df = pd.DataFrame(brands_flattened)
brand_field_names = [
    'brand_id',
    'barcode',
    'category',
    'category_code',
    'cpg_id',
    'cpg_ref',
    'name',
    'top_brand',
    'brand_code'
]
brands_df.columns = brand_field_names
analyze_and_save_df(brands_df, 'brands')

#TODO Build out transforms for receipt_bonus_point_reasons

logger.info('---COMPLETE---')

#TODO Testing

