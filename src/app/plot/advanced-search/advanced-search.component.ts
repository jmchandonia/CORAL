import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';

@Component({
  selector: 'app-advanced-search',
  templateUrl: './advanced-search.component.html',
  styleUrls: ['./advanced-search.component.css']
})
export class AdvancedSearchComponent implements OnInit {

  private dataTypeList: Array<Select2OptionData> = [
    {
      id: '0',
      text: 'N-dimensional array'
    },
    {
      id: '1',
      text: 'Graph'
    },
    {
      id: '2',
      text: 'Cluster'
    }
  ]

  constructor() { }

  ngOnInit() {
  }

}
