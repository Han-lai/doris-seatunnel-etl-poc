import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 創建繪圖畫布
fig, axs = plt.subplots(1, 2, figsize=(16, 8))

# 左側圖：Metric Store
axs[0].set_title('Metric Store')
axs[0].set_xlim(0, 10)
axs[0].set_ylim(0, 10)
axs[0].axis('off')

# 繪製中央控制系統（工廠）
factory = patches.Rectangle((4, 6), 2, 2, edgecolor='black', facecolor='lightgray')
axs[0].add_patch(factory)
axs[0].text(5, 7, '中央控制系統\n(Metric Store)', horizontalalignment='center', verticalalignment='center')

# 繪製三條生產線
for i, line in enumerate(['A', 'B', 'C']):
    # 生產線
    line_rect = patches.Rectangle((1 + i*3, 2), 2, 1, edgecolor='black', facecolor='lightblue')
    axs[0].add_patch(line_rect)
    axs[0].text(2 + i*3, 2.5, f'生產線 {line}', horizontalalignment='center', verticalalignment='center')
    
    # 數據流箭頭（上行）
    axs[0].arrow(2 + i*3, 3, 0, 3, head_width=0.3, head_length=0.3, fc='black', ec='black')
    axs[0].text(2 + i*3, 5, '數據流', horizontalalignment='center', verticalalignment='center')
    
    # 統一數據箭頭（下行）
    axs[0].arrow(2 + i*3, 6, 0, -3, head_width=0.3, head_length=0.3, fc='black', ec='black')

# 右側圖：Semantic Layer
axs[1].set_title('Semantic Layer')
axs[1].set_xlim(0, 10)
axs[1].set_ylim(0, 10)
axs[1].axis('off')

# 繪製作業手冊
handbook = patches.Rectangle((4, 6), 2, 2, edgecolor='black', facecolor='lightgreen')
axs[1].add_patch(handbook)
axs[1].text(5, 7, '作業手冊\n(Semantic Layer)', horizontalalignment='center', verticalalignment='center')

# 繪製三條生產線
for i, line in enumerate(['A', 'B', 'C']):
    # 生產線
    line_rect = patches.Rectangle((1 + i*3, 2), 2, 1, edgecolor='black', facecolor='lightblue')
    axs[1].add_patch(line_rect)
    axs[1].text(2 + i*3, 2.5, f'生產線 {line}', horizontalalignment='center', verticalalignment='center')
    
    # 操作程序箭頭（每條生產線都有一本作業手冊）
    axs[1].arrow(5, 6, -3 + i*3, -3, head_width=0.3, head_length=0.3, fc='black', ec='black')
    axs[1].text(2 + i*3, 5, '操作程序', horizontalalignment='center', verticalalignment='center')

# 顯示圖表
plt.tight_layout()
plt.show()