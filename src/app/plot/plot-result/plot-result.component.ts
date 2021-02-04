import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Router, ActivatedRoute } from '@angular/router';
import { NgxSpinnerService } from 'ngx-spinner';
import { CoreTypePlotBuilder } from 'src/app/shared/models/core-type-plot-builder';
import { PlotlyBuilder } from 'src/app/shared/models/plotly-builder';
import { PlotlyData, PlotlyLayout } from 'plotly.js';
import { TooltipDirective } from 'ngx-bootstrap/tooltip';

@Component({
  selector: 'app-plot-result',
  templateUrl: './plot-result.component.html',
  styleUrls: ['./plot-result.component.css']
})
export class PlotResultComponent implements OnInit {

  constructor(
    private plotService: PlotService,
    private router: Router,
    private route: ActivatedRoute,
    private spinner: NgxSpinnerService
    ) { }
  plotData: any;
  corePlot = false;
  coreTypePlotBuilder: CoreTypePlotBuilder;
  coreTypeName: string;
  objectId: string;
  loading = false;
  data: PlotlyData;
  layout: PlotlyLayout = {
    height: 600,
  };
  plot: PlotlyBuilder;
  shareableLink = false;
  @ViewChild(TooltipDirective) copyLink: TooltipDirective;

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.objectId = params.id;
    });

    this.route.queryParams.subscribe(queryParams => {
      if (queryParams['coreType']) {
        this.corePlot = true;
        this.coreTypeName = queryParams['coreType'];
      }
      if (queryParams['zip']) {
        this.shareableLink = true;
        this.plot = this.createPlotFromLink(decodeURIComponent(queryParams.zip));
      }
    })

    if (!this.shareableLink) {
      this.plot = Object.assign(new PlotlyBuilder(), JSON.parse(localStorage.getItem('plotlyBuilder')));
    }
    this.getPlotData();
  }

  getPlotData() {
    window.scroll(0, 0);
    this.loading = true;
    this.spinner.show();
    if (!this.corePlot) {
      // this.plotService.getDynamicPlot(this.objectId)
      this.plotService.getDynamicPlot(this.plot)
        .subscribe((data: any) => {
          const results = data.res;
          if (this.plot.plot_type.name === '1D Heatmap') {
            this.data = [{
              ...this.plot.plot_type.plotly_trace,
              x: results[0].x,
              z: [results[0].y]
            }];
          } else {
            this.data = results.map(result => {
              const trace = {
                ...result,
                ...this.plot.plot_type.plotly_trace,
                name: result.label.replace(/#VAR =/g, ''),
                error_x: {
                  type: 'data',
                  array: result.error_x,
                  visible: this.plot.axes.x.show_err_margin,
                  thickness: 0.75
                },
                error_y: {
                  type: 'data',
                  array: result.error_y,
                  visible: this.plot.axes.y.show_err_margin,
                  thickness: 0.75
                }
              };
              if (this.plot.plot_type.name === 'Horizontal Barchart') {
                const x = trace.x;
                trace.x = trace.y;
                trace.y = x;
              }
              return trace;
            });
          }
          this.layout = {
            ...this.layout,
            ...this.plot.plot_type.plotly_layout,
            legend: {
              orientation: 'h',
              y: -0.5
            },
            title: this.plot.title,
            xaxis: {
              autorange: true,
              automargin: true,
              title: this.plot.axes.x.show_title ? this.plot.axes.x.title : '',
            },
            yaxis: {
              autorange: true,
              automargin: true,
              title: this.plot.axes.y.show_title ? this.plot.axes.y.title : ''
            }
          }

          if (this.plot.plot_type.name === '1D Heatmap') {
            this.layout.yaxis.ticks = '';
            this.layout.yaxis.showticklabels = false;
          }

          if(this.plot.plot_type.plotly_trace.type === 'heatmap') {
            // TODO: All of this can go in plot_tyes.json
            if (this.plot.axes.z?.logarithmic) {
              const colorScale = [];
              for (var i = 0; i < 10; i++) {
                const color = (255 / 10) * i
                colorScale.push([Math.log10(i + 1).toString(), `rgb(${color}, ${color}, ${255 - color})`]);
              }
              this.data[0].colorscale = colorScale;
            } else {
              const colorScale = [
                ['0.0', 'rgb(0,0,255)'],
                ['0.5', 'rgb(235,235,235)'],
                ['1.0', 'rgb(255,255,0)']
              ];
              this.data[0].colorscale = colorScale;
            }
            this.data[0].hoverongaps = false;

            this.layout.plot_bgcolor = '#333';
            this.layout.xaxis.gridcolor = '#444';
            this.layout.yaxis.gridcolor = '#444';
          }

          if (this.plot.axes.z?.show_title) {
            this.layout.zaxis = {title: this.plot.axes.z.title};
          }

          if (results.length > 50) {
            // if there are more than 50 results, add more height to iframe so that the legend doesnt take up all the space
            this.layout.height += 600;
          }

          if (this.plot.axes.x.logarithmic) {
            this.layout.xaxis.type = 'log';
          }

          if (!this.plot.axes.x.show_tick_labels) {
            this.layout.xaxis.showticklabels = false;
          }

          if (this.plot.axes.y.logarithmic) {
            this.layout.yaxis.type = 'log';
          }

          if (!this.plot.axes.y.show_tick_labels) {
            this.layout.yaxis.showticklabels = false;
          }
          this.loading = false;
          this.spinner.hide();
        });
    } else {
      this.plotService.getCorePlot()
        .subscribe((res: any) => {
          const { data, layout } = res.results;
          if (this.plot.plot_type.name === '1D Heatmap') { 
            this.data = [{
              ...data,
              ...this.plot.plot_type.plotly_trace,
              x: data[0].x,
              z: [data[0].y]
            }];
          } else {
            this.data = data;
          }
          this.layout = layout;
          this.loading = false;
          this.spinner.hide();
        });
    }
  }

  createPlotFromLink(queryString: string) {
    const data = JSON.parse(queryString);
    return Object.assign(new PlotlyBuilder(), {
      urlPostData: data.flt,
      object_id: this.objectId,
      plot_type: {
        plotly_data: data.plt.plotly_data,
        plotly_trace: data.plt.plotly_trace,
        name: data.plt.n
      },
      axes: Object.entries(data.axes).reduce((acc, [key, val]: any[]) => {
        return {
          ...acc,
          [key]: {
            logarithmic: val.lg,
            show_err_margin: val.e,
            show_labels: val.lb,
            show_tick_labels: val.tl,
            title: val.t,
            show_title: val.t?.length > 0
          }
        }
      }, {}),
    })
  }

  onGoBack() {
    // this.router.navigate([`plot/options/${this.objectId}`]);
    if (this.corePlot) {
      this.router.navigate(['plot/options'], {queryParams: {coreType: this.coreTypeName}});
    } else {
      this.router.navigate([`plot/options/${this.objectId}`]);
    }
  }

  getShareablePlotUrl() {
    const el = document.createElement('textarea');
    el.value = this.plot.getPlotShareableUrl();
    el.setAttribute('readonly', ''),
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    setTimeout(() => this.copyLink.hide(), 1000)
  }

}
