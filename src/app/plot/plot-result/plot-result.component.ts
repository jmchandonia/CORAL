import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ObjectGraphMapService } from 'src/app/shared/services/object-graph-map.service';

@Component({
  selector: 'app-plot-result',
  templateUrl: './plot-result.component.html',
  styleUrls: ['./plot-result.component.css']
})
export class PlotResultComponent implements OnInit {

  constructor(private objectGraphMap: ObjectGraphMapService, private chRef: ChangeDetectorRef) { }
  plotData: any;
  loading = true;
  data: any = [{x: [], y: [], type: 'scatter', mode: 'markers'}];
  layout = {
    width: 800,
    height: 600,
    title: 'Generix Plot',
    // type: 'scatter',
    // mode: 'points',
    xaxis: {
      range: [0, 100]
    },
    yaxis: {
      range: [0, 100]
    }
  };

  ngOnInit() {
    this.plotData = this.objectGraphMap.getMeasurements();
    this.data[0].x = this.plotData.x;
    this.data[0].y = this.plotData.y;
    this.chRef.detectChanges();
  }

}
