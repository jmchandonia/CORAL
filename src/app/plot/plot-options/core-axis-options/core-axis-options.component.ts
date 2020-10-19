import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-core-axis-options',
  templateUrl: './core-axis-options.component.html',
  styleUrls: ['./core-axis-options.component.css']
})
export class CoreAxisOptionsComponent implements OnInit {

  @Input() public axisOptions: any[];

  constructor() { }

  ngOnInit(): void {
  }

}
