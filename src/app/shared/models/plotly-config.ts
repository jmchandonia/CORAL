export interface PlotlyConfig {
    axis_blocks: AxisBlock[];
    description: string;
    image_tag: string;
    n_dimensions: number;
    name: string;
    plotly_layout: PlotlyLayout;
    plotly_trace: PlotlyTrace;
}

export interface AxisBlock {
    title: string;
}

export interface PlotlyLayout {
    barmode?: string;
}

export interface PlotlyTrace {
    orientation?: string;
    type?: string;
    mode?: string;
}

