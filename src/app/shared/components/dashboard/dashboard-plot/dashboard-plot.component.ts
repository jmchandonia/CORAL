import { Component, OnInit, Input } from '@angular/core';
import { PlotService } from '../../../services/plot.service';

@Component({
  selector: 'app-dashboard-plot',
  templateUrl: './dashboard-plot.component.html',
  styleUrls: ['./dashboard-plot.component.css']
})
export class DashboardPlotComponent implements OnInit {

  @Input() id: string;

  data: any;
  layout: any;

  constructor(
    private plotService: PlotService
  ) { }

  ngOnInit() {
    if (this.id) {
      this.plotService.getReportPlotData(this.id)
        .subscribe((res: any) => {
          console.log('RES', res);
        });
    }
  }

}
