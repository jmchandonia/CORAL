import { Component, OnInit, Input, Output, EventEmitter, ViewEncapsulation, OnDestroy } from '@angular/core';
import { BrickDimension, DimensionVariable, Term } from 'src/app/shared/models/brick';
import { Subscription } from 'rxjs';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

@Component({
  selector: 'app-dimension-form',
  templateUrl: './dimension-form.component.html',
  styleUrls: ['./dimension-form.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class DimensionFormComponent implements OnInit, OnDestroy {

  private _dimension: BrickDimension;
  selectedType: string;
  error = false;
  errorSub: Subscription;
  data: Array<{id: string, text: string; has_units: boolean}> = [];
  loading = false;

  @Input() set dimension(d: BrickDimension) {
    this._dimension = d;

    if (d.type) {
      this.data = [d.type];
      this.selectedType = d.type.id;
    }
  }

  get dimension() {
    return this._dimension;
  }

  @Output() deleted = new EventEmitter();
  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
  ) { }

  ngOnInit() {
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => {
        this.error = error;
      });
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  handleSearch(event) {
    if (event.term.length) {
      this.loading = true;
      this.uploadService.searchDimensionMicroTypes(event.term).subscribe((data: any) => {
        this.loading = false;
        this.data = [...data.results];
      });
    }
  }

  formatOptionLabel(item) {
    // format for displaying microtype dropdown options
    return `${item.definition !== `${item.text}.` ? ` - ${item.definition}` : ''} (${item.scalar_type})`;
  }

  setDimensionType(event: Term) {
    this.dimension.type = event;
    this.validate();
  }

  addDimensionVariable() {
    this.dimension.variables.push(
      new DimensionVariable(this.dimension, this.dimension.variables.length, false)
      );
  }

  removeDimensionVariable(dimVar: DimensionVariable) {
    this.dimension.variables = this.dimension.variables.filter(item => item !== dimVar);
    this.dimension.resetDimVarIndices();
    this.validate();
  }

  resetDimensionVariable(event: DimensionVariable, index: number) {
    this.dimension.variables.splice(index, 1, event);
  }

  delete() {
    this.deleted.emit(this.dimension);
  }

  validate() {
    if (this.error) {
      this.validator.validateDimensions();
    }
  }

}
