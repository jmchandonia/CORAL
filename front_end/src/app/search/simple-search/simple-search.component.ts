import { Component, OnInit } from '@angular/core';
// import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryMatch, QueryParam } from '../../shared/models/QueryBuilder';
import { Router } from '@angular/router';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-simple-search',
  templateUrl: './simple-search.component.html',
  styleUrls: ['./simple-search.component.css']
})
export class SimpleSearchComponent implements OnInit {

  // dataTypeList: Array<Select2OptionData> = [{id: '', text: ''}];
  dataTypes: any[];
  selectedDataType: string;
  keywords = '';
  // select2Options: Select2Options = {
  //   width: '100%',
  //   placeholder: 'Select a Data Type from our system',
  //   containerCssClass: 'select2-custom-container'
  // };
  // ajaxOptions: Select2AjaxOptions;
  queryMatch: QueryMatch = new QueryMatch();
  queryBuilderObject: QueryBuilder;

  constructor(
    private queryBuilder: QueryBuilderService,
    private router: Router
  ) { }

  ngOnInit() {
    this.queryBuilderObject = this.queryBuilder.getCurrentObject();
    // this.queryBuilderObject = getQuery.qb;
    // if (!getQuery.empty && getQuery.qb.queryMatch) {
    //   const p = this.queryBuilderObject.queryMatch.params;
    //   if (p && p.length) {
    //     this.keywords = p[0].keyword;
    //   }
    //   this.selectedDataType = this.queryBuilderObject.queryMatch.dataType;
    //   this.dataTypeList.push({id: '0', text: this.selectedDataType});
    // }
    // this.ajaxOptions = {
    //   url: `${environment.baseURL}/data_types`,
    //   dataType: 'json',
    //   delay: 250,
    //   cache: false,
    //   processResults: (data: any) => {
    //     this.dataTypes = data.results;
    //     return {
    //       results: $.map(data.results, (obj, idx) => {
    //         return {id: idx.toString(), text: obj.dataType};
    //       }),
    //     };
    //   },
    // };
    // this.select2Options.ajax = this.ajaxOptions;
  }

  updateDataModel(event) {
    const d = this.dataTypes[parseInt(event.value, 10)];
    const { dataModel, dataType, category } = d;
    this.queryMatch.dataModel = dataModel;
    this.queryMatch.dataType = dataType;
    this.queryMatch.category = category;
  }

  onSubmit() {
    this.queryMatch.params.push(new QueryParam(null, null, this.keywords, 'string'));
    this.queryBuilderObject.queryMatch = this.queryMatch;
    // this.queryBuilder.submitSearchResults();
    this.router.navigate(['/search/result']);
    this.queryBuilder.setSearchType('simple');
  }

}
