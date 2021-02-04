import { Component, OnInit, OnDestroy } from '@angular/core';
import { PlotService } from 'src/app/shared/services/plot.service';

@Component({
  selector: 'app-plot',
  templateUrl: './plot.component.html',
  styleUrls: ['./plot.component.css']
})
export class PlotComponent implements OnInit {

  constructor(private plotService: PlotService) { }

  ngOnInit() {
  }

  ngOnDestroy() {
    this.plotService.deletePlotBuilder()
  }

}
