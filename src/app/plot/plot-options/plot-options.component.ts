import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ObjectGraphMapService } from '../../shared/services/object-graph-map.service';
import { ObjectMetadata } from '../../shared/models/object-metadata';
import { Select2OptionData } from 'ng2-select2';
import { FormBuilder, FormGroup, FormControl, FormArray } from '@angular/forms';

@Component({
  selector: 'app-plot-options',
  templateUrl: './plot-options.component.html',
  styleUrls: ['./plot-options.component.css'],
})
export class PlotOptionsComponent implements OnInit {

  private dimensions = ['x', 'y', 'z'];
  private plotObject: ObjectMetadata;
  private plotTypeOptions: Array<Select2OptionData> = [{id: '', text: ''}];
  private formDimensions: FormArray;
  private testForm: any;
  private plotForm = this.fb.group({
    plotType: '',
    graphTitle: [''],
    dimensions: this.fb.array([])
  });

  constructor(
    private route: ActivatedRoute,
    private objectGraphMap: ObjectGraphMapService,
    private fb: FormBuilder,
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
    this.addDimensions();

    this.testForm = JSON.stringify(this.plotForm.value);
  }

  addDimensions() {
    this.formDimensions = this.plotForm.get('dimensions') as FormArray;
    this.plotObject.dimensions.forEach(dimension => {
      this.formDimensions.push(this.createDimensionItem());
    });
  }

  createDimensionItem() {
    return this.fb.group({
      fromDimension: '',
      displayValuesFrom: this.fb.array([]),
      displayAxisLabels: false,
      displayAxisLabelsAs: this.fb.array([]),
      displayHoverLabels: false,
      displayHoverLabelsAs: '',
      displayAxisTitle: false,
      axisTitle: ''
    });
  }

  updatePlotType(event) {
    this.plotForm.controls.plotType.setValue(event.data[0].text);
  }

  submit() {
    // this.objectGraphMap.submitNewPlot(this.plotForm);
    console.log('plot form', this.plotForm);
  }

}
