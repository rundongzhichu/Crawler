import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 折线图
# 示例数据（每行代表一个观察对象）
df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Math': [85, 72, 90],
    'Physics': [78, 85, 82],
    'Chemistry': [92, 68, 88]
})

# 设置图形
fig, ax = plt.subplots(figsize=(10, 6))
x_labels = ['Math', 'Physics', 'Chemistry']
x_pos = np.arange(len(x_labels))  # x轴位置

# 为每一行创建一条线
for idx, row in df.iterrows():
    ax.plot(x_pos, row[['Math', 'Physics', 'Chemistry']],
            marker='o',
            label=row['Name'])

# 装饰图形
ax.set_xticks(x_pos)
ax.set_xticklabels(x_labels)
ax.set_ylabel('Score')
ax.set_title('Student Scores by Subject')
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.show()


# 条形图
# 设置条形图参数
bar_width = 0.25
x_pos = np.arange(len(df))  # 学生位置

# 为每个科目创建一组条形
for i, subject in enumerate(['Math', 'Physics', 'Chemistry']):
    plt.bar(x_pos + i*bar_width,
            df[subject],
            width=bar_width,
            label=subject)

# 装饰图形
plt.xlabel('Students')
plt.xticks(x_pos + bar_width, df['Name'])
plt.ylabel('Score')
plt.title('Subject Scores by Student')
plt.legend()
plt.tight_layout()
plt.show()


# seaborn图
import seaborn as sns

# 将数据转为长格式
melted_df = df.melt(id_vars='Name',
                   var_name='Subject',
                   value_name='Score')

# 绘制点线图
sns.pointplot(x='Subject', y='Score', hue='Name',
              data=melted_df, markers=['o', 's', 'D'])
plt.title('Student Performance Across Subjects')
plt.legend(bbox_to_anchor=(1.05, 1))
plt.tight_layout()
plt.show()

# 子图
# 创建子图网格
fig, axes = plt.subplots(nrows=len(df), figsize=(8, 10))

# 为每个学生创建单独的子图
for idx, (name, row) in enumerate(df.set_index('Name').iterrows()):
    axes[idx].bar(['Math', 'Physics', 'Chemistry'], row)
    axes[idx].set_title(f'{name}\'s Scores')
    axes[idx].set_ylim(0, 100)

plt.tight_layout()
plt.show()


# 雷达图
# 准备数据
categories = ['Math', 'Physics', 'Chemistry']
N = len(categories)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()

# 创建极坐标图
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, polar=True)

# 为每个学生绘制雷达图
for idx, row in df.iterrows():
    values = row[categories].tolist()
    values += values[:1]  # 闭合图形
    ax.plot(angles + angles[:1], values, 'o-', label=row['Name'])
    ax.fill(angles + angles[:1], values, alpha=0.1)

# 装饰图形
ax.set_theta_offset(np.pi/2)
ax.set_theta_direction(-1)
ax.set_thetagrids(np.degrees(angles), categories)
ax.set_title('Student Performance Radar Chart', pad=20)
ax.legend(bbox_to_anchor=(1.1, 1.1))
plt.show()