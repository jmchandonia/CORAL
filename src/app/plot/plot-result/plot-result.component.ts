import { Component, OnInit, OnDestroy } from '@angular/core';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Router, ActivatedRoute } from '@angular/router';
import { NgxSpinnerService } from 'ngx-spinner';

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
  objectId: string;
  loading = false;
  data: any;
  layout: any = {
    width: 800,
    height: 600,
  };

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.objectId = params.id;
    });
    this.getPlotData();
  }

  getPlotData() {
    window.scroll(0, 0);
    this.loading = true;
    this.spinner.show();
    this.plotService.getPlotlyData()
      .subscribe((res: any) => {
        const { data, layout } = res.results;
        this.data = data;
        this.layout = layout;
        if (this.layout.yaxis) { this.layout.yaxis.automargin = true; }
        if (this.layout.xaxis) { this.layout.xaxis.automargin = true; }
        this.loading = false;
        this.spinner.hide();
      });
  }

  onGoBack() {
    this.router.navigate([`plot/options/${this.objectId}`]);
  }

}
