import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv('../data/processed/wildfire_dataset.csv', low_memory=False)

order = ['A', 'B', 'C', 'D+']
colors = ['#fd8d3c', '#e6550d', '#b5360a', '#7f2704']   
weather = ['temp_max_mean_7d', 'previous_day_temp_max', 'rh_min_mean_7d', 'previous_day_rh_min',
           'vpd_max_7d', 'et0_sum_7d', 'precipitation_sum_7d', 'dry_days_7d',
           'wind_speed_max_7d', 'wind_gust_max_7d', 'cell_elevation_m']


# 1. target variable: class imbalance 
counts = df['size_class'].value_counts().reindex(order)
fractions = df['size_class'].value_counts(normalize=True).reindex(order)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].pie(counts, labels=[f'{c}  {f:.1%}' for c, f in fractions.items()], colors=colors,
            startangle=20, counterclock=False)
axes[0].set_title('share of fires per size class')
counts.plot.bar(ax=axes[1], color=colors, rot=0)
axes[1].set_xlabel('size class')
axes[1].set_ylabel('number of fires')
axes[1].set_title('number of fires per size class')
plt.savefig('../figures/1_size_class.png', dpi=200, bbox_inches='tight')
plt.close()


# 2. continuous features vs size_class 
fig, axes = plt.subplots(3, 4, figsize=(14, 9))   
for ax, col in zip(axes.ravel(), weather):
    bp = df.boxplot(column=col, by='size_class', ax=ax, showfliers=False, patch_artist=True,
                    return_type='dict', color={'medians': 'white'})[col]
    for box, color in zip(bp['boxes'], colors):   
        box.set_facecolor(color)
axes[2, 3].axis('off')
plt.suptitle('features by size class')
plt.tight_layout()
plt.savefig('../figures/2_boxplots.png', dpi=200, bbox_inches='tight')
plt.close()


# 3. categorical features vs size_class 
df['fuel_group'] = df['fuel_group'].fillna('Missing')
df['landowner_category'] = df['landowner_category'].fillna('Missing')

fig, axes = plt.subplots(2, 2, figsize=(13, 9))
for ax, col in zip(axes.ravel(), ['fire_cause', 'state', 'landowner_category', 'fuel_group']):
    count_matrix = df.groupby([col, 'size_class']).size().unstack(fill_value=0)[order]
    count_matrix = count_matrix[count_matrix.sum(axis=1) >= 300]   # drop tiny categories
    count_matrix_norm = count_matrix.div(count_matrix.sum(axis=1), axis=0).sort_values('D+')
    count_matrix_norm.plot(kind='barh', stacked=True, ax=ax, color=colors, legend=False)
    ax.set_title(col)
    ax.set_xlabel('fraction of fires')
    ax.set_ylabel('')
axes[0, 1].legend(title='size class', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.savefig('../figures/3_categorical.png', dpi=200, bbox_inches='tight')
plt.close()


# 4. temporal patterns 
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
df['month'].value_counts().sort_index().plot.bar(ax=axes[0], color=colors[1], rot=0)
axes[0].set_xlabel('month')
axes[0].set_ylabel('number of fires')
axes[0].set_title('fires per month')
for ax, col in zip(axes[1:], ['month', 'year']):
    count_matrix = df.groupby([col, 'size_class']).size().unstack()[order]
    count_matrix_norm = count_matrix.div(count_matrix.sum(axis=1), axis=0)
    count_matrix_norm.plot(kind='bar', stacked=True, ax=ax, color=colors, rot=0, legend=False)
    ax.set_ylabel('fraction of fires')
    ax.set_title(f'size class balance per {col}')
axes[2].legend(title='size class', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout()
plt.savefig('../figures/4_temporal.png', dpi=200, bbox_inches='tight')
plt.close()
