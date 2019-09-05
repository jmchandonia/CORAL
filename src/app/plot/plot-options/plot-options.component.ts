import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ObjectGraphMapService } from '../../shared/services/object-graph-map.service';
import { ObjectMetadata } from '../../shared/models/object-metadata';
import { Select2OptionData } from 'ng2-select2';

@Component({
  selector: 'app-plot-options',
  templateUrl: './plot-options.component.html',
  styleUrls: ['./plot-options.component.css']
})
export class PlotOptionsComponent implements OnInit {

  private dimensions = ['x', 'y', 'z'];
  private plotObject: ObjectMetadata;
  private plotTypeOptions: Array<Select2OptionData> = [{id: '', text: ''}];

  constructor(
    private route: ActivatedRoute,
    private objectGraphMap: ObjectGraphMapService
    ) { }
  private objectId: string;

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.objectId = params.id;
    });
    this.plotObject = this.objectGraphMap.getSelectedObject();
    const dropDownItems = this.objectGraphMap.listPlotTypes();
    dropDownItems.forEach((val, idx) => {
      this.plotTypeOptions.push({ id: idx.toString(), text: val });
    });
  }

}
