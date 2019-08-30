import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryParam, QueryMatch } from '../../shared/models/QueryBuilder';

@Component({
  selector: 'app-advanced-search',
  templateUrl: './advanced-search.component.html',
  styleUrls: ['./advanced-search.component.css']
})
export class AdvancedSearchComponent implements OnInit {

  private queryBuilderObject: QueryBuilder;

  constructor(private queryBuilder: QueryBuilderService) { }

  ngOnInit() {

    this.queryBuilderObject = this.queryBuilder.getCurrentObject();

    this.queryBuilder.getUpdatedObject().subscribe(object => {
      Object.assign(this.queryBuilderObject, object);
    });
  }

  addProcess(process, queryParam) {
    this.queryBuilder.addProcessParam(process, queryParam);
  }

  updateProcess(process, index, queryParam) {
    this.queryBuilder.updateProcessParam(process, index, queryParam);
  }

  removeProcess(process, queryParam) {
    this.queryBuilder.removeProcessParam(process, queryParam);
  }

  testObject() {
    console.log('QBO -> ',  JSON.stringify(this.queryBuilderObject));
  }

}
