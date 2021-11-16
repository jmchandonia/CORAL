import {
  Component,
  OnInit,
  OnDestroy,
  Input,
  Output,
  EventEmitter,
 } from '@angular/core';
import { QueryParam } from '../../../../shared/models/QueryBuilder';
import { QueryBuilderService } from '../../../../shared/services/query-builder.service';
import { BsDatepickerConfig } from 'ngx-bootstrap/datepicker';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-property-params',
  templateUrl: './property-params.component.html',
  styleUrls: ['./property-params.component.css'],
})
export class PropertyParamsComponent implements OnInit, OnDestroy {

  @Output() removed: EventEmitter<any> = new EventEmitter();
  @Input() queryParam: QueryParam;
  @Input() dataType: string;

  propertyTypes: any[] = [];
  matchTypes: string[];
  selectedMatchType: string;
  selectedAttribute: string;
  private invalidQuerySub: Subscription;
  public valid = true;

  constructor(
    private queryBuilder: QueryBuilderService
  ) {
  }

  datepickerConfig: Partial<BsDatepickerConfig> = {
    containerClass: 'theme-dark-blue',
    useUtc: true
  };

  ngOnInit() {
    this.selectedMatchType = this.queryParam.matchType;
    const attributes = this.queryBuilder.getAttributes(this.dataType);
    if (this.queryParam.attribute) {
      this.selectedAttribute = this.queryParam.attribute;
      this.setOperators();
    }
    this.propertyTypes = [...attributes];
    this.invalidQuerySub = this.queryBuilder.getValidationSub()
      .subscribe((valid) => this.valid = valid);
   }

  ngOnDestroy() {
    if (this.invalidQuerySub) {
      this.invalidQuerySub.unsubscribe();
    }
  }

  removeParam() {
    this.removed.emit();
  }

  setAttribute(event) {
    this.queryParam.attribute = event.name;
    this.queryParam.scalarType = event.scalar_type
    this.setOperators();
  }

  setOperators() {
    this.matchTypes = this.queryBuilder.getOperators(this.queryParam);
  }

  setMatchType(event) {
    this.queryParam.matchType = event
  }

  handleDateSelected(event: Date) {
    if (!event) return;
    this.queryParam.keyword = event.toISOString().split('T')[0];
  }

  get invalidKeyword() {
    if (!this.queryParam.keyword?.length) return true;
    if (this.queryParam.scalarType === 'int' || this.queryParam.scalarType === 'float') {
      return isNaN(parseInt(this.queryParam.keyword));
    }
    return false;
  }

}
