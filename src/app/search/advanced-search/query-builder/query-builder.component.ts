import { Component, OnInit, Input, Output, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { Select2OptionData, } from 'ng2-select2';
import { QueryMatch, QueryParam } from '../../../shared/models/QueryBuilder';
import { NetworkService } from '../../../shared/services/network.service';
import { QueryBuilderService } from '../../../shared/services/query-builder.service';
import { HttpClient } from '@angular/common/http';
import * as $ from 'jquery';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-query-builder',
  templateUrl: './query-builder.component.html',
  styleUrls: ['./query-builder.component.css']
})
export class QueryBuilderComponent implements OnInit {

  private queryMatch: QueryMatch = new QueryMatch(); // need to program in dataType
  // make queryMatch input a set function that assigns data value to this.queryMatch
  // @Input() set data(qMatch: QueryMatch) { this.queryMatch = qMatch }
  @Input() connection: string;
  @Output() create: EventEmitter<QueryMatch> = new EventEmitter();
  @Input() operators = [];
  private ajaxOptions: Select2AjaxOptions;
  private selectedAttributes: any;
  private dataModels: any;
  private dataTypes: any;

  options: Select2Options = {
    width: '100%',
    placeholder: 'Select A DataType',
    templateResult: state => {
      return `<span><img class="icon" src="./assets/${state.text.includes('u') ? 'Brick' : 'Sample'}.png" />${state.text}</span>`;
    },
    escapeMarkup: m => m
  };

  private dataModelList: Array<Select2OptionData> = [
    {
      id: '',
      text: ''
    },
  ];

  private propertyParams = [
    {
      type: '',
      match: 'contains',
      keyword: ''
    }
  ];

  constructor(
    private queryBuilder: QueryBuilderService,
    private network: NetworkService,
    private http: HttpClient,
    private chRef: ChangeDetectorRef
  ) { }

  public formatState(state) {
    const $state = 
      `<span><img class="icon" src="./assets/${state.text.includes('u') ? 'Brick' : 'Sample'}.png />${state.text}</span>`;
    return $state;
  }

  ngOnInit() {
    this.http.get('https://psnov1.lbl.gov:8082/generix/data_models')
      .subscribe((data: any) => {
        console.log('DATA_MODELS_RESULT', data);
        this.dataModels = data.results;
      });

    this.ajaxOptions = {
      url: 'https://psnov1.lbl.gov:8082/generix/data_types',
      dataType: 'json',
      delay: 250,
      cache: false,
      processResults: (data: any) => {
        console.log('DATA_TYPES_RESULT', data);
        this.dataTypes = data.results;
        return {
          results: $.map(data.results, (obj, idx) => {
            return {id: idx.toString(), text: obj.dataType};
          }),
        };
    },
  };

    this.options.ajax = this.ajaxOptions;
}

  /// ADD SCALAR TYPE IN PARAMETERS WITH ATTRIBUTES
  // https://psnov1.lbl.gov:8082/generix/search_operations
  /// ADD ICONS FOR SEARCH PARAMS

  updateObjectDataModel(event) {
    const selected = this.dataTypes[parseInt(event.value, 10)];
    const selectedModel = this.dataModels[selected.dataModel];
    this.queryMatch.dataModel = selectedModel.dataModel;
    this.queryMatch.dataType = event.data[0].text;
    this.queryMatch.category = selectedModel.category;
    this.selectedAttributes = selectedModel.properties;
    this.queryMatch.params = [];
    // make dropdown for propertyparams disabled until this is selected
    // remove old propertyparam references is a new type is selected
    this.updateQueryMatch();
  }

  updatePropertyParam(index, event) {
    this.queryMatch.params[index][event.key] = event.value.data[0].text;
    this.updateQueryMatch();
  }

  removePropertyParam(param) {
    this.queryMatch.params = this.queryMatch.params.filter(p => p !== param);
    this.updateQueryMatch();
  }

  addPropertyParam(param) {
    this.queryMatch.params.push(param);
    this.updateQueryMatch();
  }

  updateQueryMatch() {
    this.queryBuilder.updateQueryMatch(this.connection, this.queryMatch);
  }

}
