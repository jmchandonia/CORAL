import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-plot-result',
  templateUrl: './plot-result.component.html',
  styleUrls: ['./plot-result.component.css']
})
export class PlotResultComponent implements OnInit {

  constructor() { }
  private loading = true;
  private data: any;
  private layout = {
    width: 800,
    height: 600,
    title: 'Generix Plot'
  };

  ngOnInit() {
  }

}
