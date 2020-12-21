import { Component, OnInit, OnDestroy } from '@angular/core';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Router, ActivatedRoute } from '@angular/router';
import { NgxSpinnerService } from 'ngx-spinner';
import { CoreTypePlotBuilder } from 'src/app/shared/models/core-type-plot-builder';
import { PlotlyBuilder } from 'src/app/shared/models/plotly-builder';

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
  data: any;
  layout: any = {
    width: 800,
    height: 600,
  };
  plot: PlotlyBuilder;

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.objectId = params.id;
    });

    this.route.queryParams.subscribe(queryParams => {
      if (queryParams['coreType']) {
        this.corePlot = true;
        this.coreTypeName = queryParams['coreType'];
      }
    })
    this.plot = JSON.parse(localStorage.getItem('plotlyBuilder'));
    this.getPlotData();
  }

  getPlotData() {
    window.scroll(0, 0);
    this.loading = true;
    this.spinner.show();
    if (!this.corePlot) {
      this.plotService.getDynamicPlot(this.objectId)
        .subscribe((data: any) => {
          const results = data.res;
          this.data = results.map(result => {
            const trace = {
              ...result,
              ...this.plot.plot_type.plotly_trace,
              name: result.label,
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
            return trace;
          });
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
              title: this.plot.axes.x.show_title ? this.plot.axes.x.title : '',
            },
            yaxis: {
              autorange: true,
              title: this.plot.axes.y.show_title ? this.plot.axes.y.title : ''
            }
          }

          if (this.plot.axes.z?.show_title) {
            this.layout.zaxis = {title: this.plot.axes.z.title};
          }

          if (results.length > 4) {
            // add 16px for every extra tracelabel (prevents plot from being squeezed up in the top)
            this.layout.height += (16 * (results.length - 4));
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

          if (!this.plot.axes.x.show_tick_labels) {
            this.layout.yaxis.showticklabels = false;
          }
          this.loading = false;
          this.spinner.hide();
        });
    } else {
      this.plotService.getCorePlot()
        .subscribe((res: any) => {
          const { data, layout } = res.results;
          this.data = data;
          this.layout = layout;
          this.loading = false;
          this.spinner.hide();
        });
    }
  }

  onGoBack() {
    // this.router.navigate([`plot/options/${this.objectId}`]);
    if (this.corePlot) {
      this.router.navigate(['plot/options'], {queryParams: {coreType: this.coreTypeName}});
    } else {
      this.router.navigate([`plot/options/${this.objectId}`]);
    }
  }

}
