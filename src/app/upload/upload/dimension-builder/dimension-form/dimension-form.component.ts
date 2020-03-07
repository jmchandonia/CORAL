import { Component, OnInit, Input, Output, EventEmitter, ViewEncapsulation, OnDestroy } from '@angular/core';
import { BrickDimension, DimensionVariable, Term } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
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

  select2Options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term) {
        options.callback({results: []});
      } else {
        this.uploadService.searchDimensionMicroTypes(term)
          .subscribe((data: any) => {
            options.callback({results: data.results as Select2OptionData});
          });
      }
    }
  };

  selectedType: string;
  error = false;
  errorSub: Subscription;
  data: Array<Select2OptionData> = [];

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

  setDimensionType(event) {
    const term = event.data[0];
    this.dimension.type = new Term(term.id, term.text);
    this.validate();
  }

  addDimensionVariable() {
    this.dimension.variables.push(
      new DimensionVariable(this.dimension, this.dimension.variables.length, false)
      );
  }

  removeDimensionVariable(dimVar) {
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
