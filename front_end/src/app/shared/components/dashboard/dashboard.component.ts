import { Component, OnInit } from '@angular/core';
import { PlotService } from '../../services/plot.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {

  constructor(
    // private plotService: PlotService
  ) { }

  ngOnInit() {
  }

}
