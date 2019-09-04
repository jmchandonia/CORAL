import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-plot-options',
  templateUrl: './plot-options.component.html',
  styleUrls: ['./plot-options.component.css']
})
export class PlotOptionsComponent implements OnInit {

  private dimensions = ['X', 'Y'];

  constructor(private route: ActivatedRoute) { }
  private objectId: string;

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.objectId = params.id;
    });
  }

}
