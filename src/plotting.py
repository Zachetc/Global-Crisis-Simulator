import matplotlib.pyplot as plt

def plot_series(y, title, outpath):
    plt.figure()
    plt.plot(y)
    plt.xlabel("Day")
    plt.ylabel("Shortage %")
    plt.title(title)
    plt.ylim(0, 1)
    plt.savefig(outpath, dpi=160, bbox_inches="tight")
    plt.close()
