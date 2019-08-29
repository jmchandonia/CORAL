import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css']
})
export class PropertyParamsComponent implements OnInit {

  @Output() removed: EventEmitter<any> = new EventEmitter();

  private propertyTypes: Array<Select2OptionData> = [
    {
      id: '0',
      text: 'name'
    },
    {
      id: '1',
      text: 'campaign name'
    },
    {
      id: '2',
      text: 'created by'
    },

  ]

  private matchTypes: Array<Select2OptionData> = [
    {
      id: '0',
      text: 'Match'
    },
    {
      id: '1',
      text: 'Contains'
    }
  ]

  @Input() data = {
    type: '', 
    match: 'contains',
    keyword: ''
  }

  constructor() { }

  ngOnInit() {
  }

  removeParam() {
    this.removed.emit();
  }

}
