import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def split_red(cp_src_df: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame()
    df['code'] = cp_src_df['code']
    for i in range(0, 6, 1):
        df[f'red{i+1}'] = cp_src_df["red"].apply(lambda v: int(v.split(",")[i]))
    df["blue"] = cp_src_df["blue"]
    return df

if __name__ == '__main__':
    # 读取整个文件（默认读取第一个Sheet）
    df_source = pd.read_excel("output.xlsx", header=0, sheet_name="ssq_sheet")  # 文件路径
    # 显示前5行数据
    # print("展示数据：")
    # print(df_source.to_markdown(tablefmt="grid"))

    # 每一期叠加到一起画图
    num_end = 1000
    num_start = 0
    com_df = split_red(df_source)
    # print(com_df.to_markdown(tablefmt="grid"))

    # 折线图
    fig, ax = plt.subplots(figsize=(10, 6))
    x_labels = ['red1', 'red2', 'red3', 'red4', 'red5', 'red6', 'blue']
    x_pos = np.arange(len(x_labels))  # x轴位置
    # 为每一行创建一条线
    for idx, row in com_df.iloc[slice(num_start, num_end, 1)].iterrows():
        ax.plot(x_pos, row[['red1', 'red2', 'red3', 'red4', 'red5', 'red6', 'blue']],
                marker='o', label=row["code"])
    # 装饰图形
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.set_ylabel('cp red blue change')
    ax.set_title('compare per issue')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()

    # # 雷达图
    # categories =  ['red1', 'red2', 'red3', 'red4', 'red5', 'red6', 'blue']
    # N = len(categories)
    # angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    # # 创建极坐标图
    # fig = plt.figure(figsize=(8, 8))
    # ax = fig.add_subplot(111, polar=True)
    # # 为每个学生绘制雷达图
    # for idx, row in com_df.iterrows():
    #     values = row[categories].tolist()
    #     values += values[:1]  # 闭合图形
    #     ax.plot(angles + angles[:1], values, 'o-', label=row["code"])
    #     ax.fill(angles + angles[:1], values, alpha=0.1)
    #
    # # 装饰图形
    # ax.set_theta_offset(np.pi / 2)
    # ax.set_theta_direction(-1)
    # ax.set_thetagrids(np.degrees(angles), categories)
    # ax.set_title('Student Performance Radar Chart', pad=20)
    # ax.legend(bbox_to_anchor=(1.1, 1.1))
    # plt.show()

# # 每一期的红蓝球放一起作为一张图
# num_cnt=2000
# for i in range(6):
#     df = pd.DataFrame({
#         f'red{i}': df_source["red"].apply(lambda v: int(v.split(",")[i]))
#     })
#
#     df["id"] = range(len(df_source) + 1, 1, -1)
#     # print(df.to_markdown(tablefmt="grid"))
#     # 折线图
#     df.head(num_cnt).plot.line(
#         x="id",
#         y=f'red{i}',
#         xlabel="issue",
#         ylabel=f"red{i}",
#         title=f"red{i} change",
#         figsize=(10, 5),
#         grid=True,
#         marker="o"  # 数据点标记
#     )
#     plt.show()
#
# df = pd.DataFrame({
#     'blue': df_source["blue"]
# })
# df["id"] = range(len(df_source) + 1, 1, -1)
# # 折线图
# df.head(num_cnt).plot.line(
#     x="id",
#     y="blue",
#     xlabel="issue",
#     ylabel="blue",
#     title="blue change",
#     figsize=(10, 5),
#     grid=True,
#     marker="o"  # 数据点标记
# )
#
# plt.show()
#
#
#
# # 每一期串起来作为一张图
# num_cnt_1=500
# df = pd.DataFrame({})
# df["comb"]=[]
# for i in range(num_cnt_1):
#     df = pd.concat([df["comb"], pd.Series(df_source["red"][i].split(",")).to_frame("comb")], axis=0).reset_index(drop=True)
#     df = pd.concat([df["comb"], pd.Series(df_source["blue"][i]).to_frame("comb")], axis=0).reset_index(drop=True)
#
#
# df = df["comb"].apply(lambda v: int(v))
# df = pd.concat([df, pd.Series(range(len(df) + 1, 1, -1)).to_frame('id')], axis=1)
# print(df.to_markdown(tablefmt="grid"))
# # 折线图
# df.head(num_cnt*7).plot.line(
#     x="id",
#     y=f'comb',
#     xlabel="issue",
#     ylabel=f"redblue",
#     title=f"redblue change",
#     figsize=(10, 5),
#     grid=True,
#     marker="o"  # 数据点标记
# )
# plt.show()
