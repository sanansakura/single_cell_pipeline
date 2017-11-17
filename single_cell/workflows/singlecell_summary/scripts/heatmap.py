'''
Created on Oct 24, 2017

@author: dgrewal
'''
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as hc
import scipy.spatial.distance as dist
from matplotlib.colors import rgb2hex
from matplotlib.colors import ListedColormap
import seaborn as sns


class ClusterMap(object):

    def __init__(self, data, colordata, vmax):
        """
        :param data pandas dataframe with bins as columns and samples as rows
        :param colordata: dict with samples and their corresponding type
                        used for adding a colorbar
        """

        self.chromosomes = [str(v) for v in range(1, 23)] + ['X', 'Y']

        self.colordata = colordata
        self.rows = data.index

        self.bins = data.columns.values

        self.data = data.as_matrix()

        self.vmax = vmax

        self.generate_plot()

    def get_chr_idxs(self, bins):
        """
        :param bins: sorted bins used for the plot
        :return chr_idxs: list with the index where chromosome changes 
        returns the index where the chromosome changes
        used for marking chr boundaries on the plot
        """
        # chr 1 starts at beginning
        chr_idxs = [0]

        chrom = '1'
        for i, bin_v in enumerate(bins):
            if bin_v[0] != chrom:
                chr_idxs.append(i)
                chrom = bin_v[0]

        return chr_idxs

    def get_cmap_colorbar(self):
        """generates listed colormap for colordata
        used to plot a color bar. using seaborn to keep colors same as old code
        :returns listedcolormap 
        :returns list of string desc for each color
        """
        ccs = list(set(self.colordata.values()))

        cmap = sns.color_palette("RdBu_d", len(ccs))

        return ListedColormap(cmap), ccs

    def generate_colormap_heatmap(self, localmax, maxval):
        """generating a custom heatmap 2:gray 0: blue 2+: reds
        :param maxval highest value in the data
        :returns listedcolormap
        """
        # all colors 2 and up are red with increasing intensity
        num_reds = maxval

        cmap = matplotlib.cm.get_cmap('Reds', num_reds)

        reds_hex = []
        for i in range(2, cmap.N):
            # will return rgba, we take only first 3 so we get rgb
            rgb = cmap(i)[:3]
            reds_hex.append(rgb2hex(rgb))

        num_reds = int(localmax-2)
        reds_hex = reds_hex[:num_reds]

        cmap = ListedColormap(['#3498DB', '#85C1E9', '#D3D3D3'] + reds_hex)

        return cmap

    def plot_dendrogram(self, fig, mat, placement):
        """plots a dendrogram
        :param fig: matplotlib figure
        :param mat: data matrix (np.array)
        :param placement: list with [x,y,w,h] values for positioning plot
        :returns linkage matrix
        """
        # placement of dendrogram on the left of the heatmap
        ax1 = fig.add_axes(placement, frame_on=True)

        # Compute and plot left dendrogram.
        linkage = hc.linkage(dist.pdist(mat), method='average')
        hc.dendrogram(linkage, orientation='left')
        ax1.set_xticks([])
        ax1.set_yticks([])
        ax1.set_facecolor("white")

        return linkage

    def plot_row_colorbar(self, fig, linkage, placement):
        """adds colorbar next to the dendrogram
        :param fig: matplotlib figure
        :param linkage matrix
        :param placement: list with [x,y,w,h] values for positioning plot
        """
        axr = fig.add_axes(placement)

        order = hc.leaves_list(linkage)
        order = [self.rows[i] for i in order]

        cmap, ccs = self.get_cmap_colorbar()

        colors = np.array([ccs.index(self.colordata[v]) for v in order])
        colors.shape = (len(colors), 1)

        axr.matshow(colors, aspect='auto', origin='lower', cmap=cmap)
        axr.set_xticks([])
        axr.set_yticks([])

        # Plot color legend
        legend_plc = [0.77, 0.98, 0.18, 0.01]
        axcb = fig.add_axes(legend_plc, frame_on=False)

        self.plot_legend(axcb, cmap, ticklabels=ccs)

    def plot_heatmap(self, fig, mat, linkage, placement):
        """adds heatmap
        :param fig: matplotlib figure
        :param data matrix
        :param linkage matrix
        :param placement: list with [x,y,w,h] values for positioning plot
        """
        axm = fig.add_axes(placement)

        vmax = np.nanmax(mat)
        cmap = self.generate_colormap_heatmap(vmax, self.vmax)

        #sort matrix based on dendrogram order
        leaves = hc.leaves_list(linkage)
        mat = mat[leaves, :]

        axm.pcolormesh(mat, cmap=cmap, rasterized=True)

        axm.set_yticks([])

        for i in range(mat.shape[0]):
            axm.text(mat.shape[1] - 0.5, i, self.rows[leaves[i]],
                     fontsize=12)

        chr_idxs = self.get_chr_idxs(self.bins)
        axm.set_xticks(chr_idxs)
        axm.set_xticklabels(self.chromosomes)

        for val in chr_idxs:
            axm.plot([val,val], [mat.shape[0],0], ':', linewidth=0.5, color='black', )

        # Plot color legend
        legend_plc = [0.07, 0.98, 0.18, 0.01]
        axcb = fig.add_axes(legend_plc, frame_on=False)
        self.plot_legend(axcb, cmap)

    def plot_legend(self, axes, cmap, ticklabels=None):
        """adds legend
        :param axes: matplotlib figure axes
        :param cmap: colormap 
        :param ticklabels: tick labels
        """
        bounds = range(cmap.N + 1)
        norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)

        cbar = matplotlib.colorbar.ColorbarBase(axes, cmap=cmap, norm=norm,
                                                orientation='horizontal')
        cbar.set_ticks([v + 0.5 for v in bounds])

        if ticklabels:
            cbar.set_ticklabels(ticklabels)
        else:
            cbar.set_ticklabels(bounds)

    def generate_plot(self):
        """generates a figure with dendrogram, colorbar, heatmap and legends
        """
        fig = plt.figure(figsize=(30, 30))

        # fig's height and starting pos
        y = 0.1
        h = 0.85

        # dendrogram figure placement on the page
        dgram_plc = [0.05, y, 0.05, h]
        linkage = self.plot_dendrogram(fig, self.data, dgram_plc)

        # colorbar placement
        # x = dgram x + dgram w + margin
        # w=colorbar width
        cbar_plc = [0.101, y, 0.015, h]
        self.plot_row_colorbar(fig, linkage, cbar_plc)

        # heatmap placement
        # x = cbar x + cbar w + margin
        #w = width
        hmap_plc = [0.117, y, 0.8, h]
        self.plot_heatmap(fig, self.data, linkage, hmap_plc)

        return fig