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
          const plotlyResult = [];
          const results = JSON.parse(data.res);
          results['values-x'].forEach((value, idx) => {
            plotlyResult.push({
              x: value,
              y: results['values-y'][idx],
              mode: 'lines', // TODO: this should be dynamic according to plot
              name: results['series-labels'][idx],
              ...this.plot.plot_type.plotly_trace
            });
          });
          this.data = plotlyResult;
          this.layout = {
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
          if (this.plot.axes.x.logarithmic) {
            this.layout.xaxis.type = 'log';
          }
          if (this.plot.axes.y.logarithmic) {
            this.layout.xaxis.type = 'log';
          }
          this.loading = false;
          this.spinner.hide();
        });
    }
    // this.plotService.getPlotlyResult()
      // .subscribe((res: any) => {
      //   const { data, layout } = res.results;
      //   this.data = data;
      //   this.layout = layout;
      //   this.loading = false;
      //   this.spinner.hide();
      // });
    // if (this.corePlot) {
    //   this.plotService.getCorePlotlyData(this.coreTypePlotBuilder)
    //     .subscribe((res: any) => {
    //       const { data, layout } = res.results;
    //       this.data = data;
    //       this.layout = layout;
    //       this.loading = false;
    //       this.spinner.hide();
    //     })
    // } else {
    //   this.plotService.getPlotlyData()
    //     .subscribe((res: any) => {
    //       const { data, layout } = res.results;
    //       this.data = data;
    //       this.layout = layout;
    //       if (this.layout.yaxis) { this.layout.yaxis.automargin = true; }
    //       if (this.layout.xaxis) { this.layout.xaxis.automargin = true; }
    //       this.loading = false;
    //       this.spinner.hide();
    //   });
    // }
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
