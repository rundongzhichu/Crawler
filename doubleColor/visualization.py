import pandas as pd
import matplotlib.pyplot as plt

# 读取整个文件（默认读取第一个Sheet）
df_source = pd.read_excel("output.xlsx", header=0, sheet_name="ssq_sheet")  # 文件路径
# 显示前5行数据
# print("展示数据：")
# print(df_source.to_markdown(tablefmt="grid"))
num_cnt=2000
for i in range(6):
    df = pd.DataFrame({
        f'red{i}': df_source["red"].apply(lambda v: int(v.split(",")[i]))
    })

    df["id"] = range(len(df_source) + 1, 1, -1)
    # print(df.to_markdown(tablefmt="grid"))
    # 折线图
    df.head(num_cnt).plot.line(
        x="id",
        y=f'red{i}',
        xlabel="issue",
        ylabel=f"red{i}",
        title=f"red{i} change",
        figsize=(10, 5),
        grid=True,
        marker="o"  # 数据点标记
    )
    plt.show()

df = pd.DataFrame({
    'blue': df_source["blue"]
})
df["id"] = range(len(df_source) + 1, 1, -1)
# 折线图
df.head(num_cnt).plot.line(
    x="id",
    y="blue",
    xlabel="issue",
    ylabel="blue",
    title="blue change",
    figsize=(10, 5),
    grid=True,
    marker="o"  # 数据点标记
)

plt.show()



num_cnt_1=500
df = pd.DataFrame({})
df["comb"]=[]
for i in range(num_cnt_1):
    df = pd.concat([df["comb"], pd.Series(df_source["red"][i].split(",")).to_frame("comb")], axis=0).reset_index(drop=True)
    df = pd.concat([df["comb"], pd.Series(df_source["blue"][i]).to_frame("comb")], axis=0).reset_index(drop=True)

df = df["comb"].apply(lambda v: int(v))
df = pd.concat([df, pd.Series(range(len(df) + 1, 1, -1)).to_frame('id')], axis=1)
print(df.to_markdown(tablefmt="grid"))
# 折线图
df.head(num_cnt*7).plot.line(
    x="id",
    y=f'comb',
    xlabel="issue",
    ylabel=f"redblue",
    title=f"redblue change",
    figsize=(10, 5),
    grid=True,
    marker="o"  # 数据点标记
)
plt.show()