import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { PlotService } from 'src/app/shared/services/plot.service';
import { Router, ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';

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
    private chRef: ChangeDetectorRef
    ) { }
  private plotSub: Subscription;
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
    this.router.navigate([`plot/options/${this.objectId}`]);
  }

}
