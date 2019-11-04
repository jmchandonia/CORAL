import { Component, OnInit, OnDestroy } from '@angular/core';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Router, ActivatedRoute } from '@angular/router';

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
    ) { }
  plotData: any;
  objectId: string;
  loading = false;
  data: any;
  layout = {
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
    this.plotService.getPlotlyData()
      .subscribe((res: any) => {
        const { data, layout } = res.results;
        this.data = data;
        this.layout = layout;
        this.loading = false;
      });
  }

  onGoBack() {
    this.router.navigate([`plot/options/${this.objectId}`]);
  }

}
