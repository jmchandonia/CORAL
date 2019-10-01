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
  loading = true;
  data: any;
  layout = {
    width: 800,
    height: 600,
  };

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.objectId = params.id;
    });


    this.plotService.getPlotlyData()
      .subscribe((data: any) => {
        const result = data.results;
        this.data = result.data;
        this.layout = result.layout;
        this.loading = false;
      });
  }

  onGoBack() {
    this.plotService.markPlotStatus();
    this.router.navigate([`plot/options/${this.objectId}`]);
  }

}
