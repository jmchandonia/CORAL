import { Component, OnInit, Input, Output, EventEmitter, OnDestroy } from '@angular/core';
import { Context, Term } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Select2OptionData } from 'ng2-select2';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-context-form',
  templateUrl: './context-form.component.html',
  styleUrls: ['./context-form.component.css']
})
export class ContextFormComponent implements OnInit, OnDestroy {


  private _context: Context;

  @Input() set context(c: Context) {
    this._context = c;

    this.typesSelect2 = c.typeTerm ? [c.typeTerm] : [];
    this.unitsSelect2 = c.units ? [c.units] : [{id: '', text: ''}];
    this.valuesSelect2 = c.value && c.requireSelect2ForVal
      ? [c.value] as Select2OptionData[]
      : [{id: '', text: ''}];

    if (c.typeTerm) {
      this.typeItem = c.typeTerm.id;
    }
    if (c.units) {
      this.unitsItem = c.units.id;
    }
    if (c.value && c.requireSelect2ForVal) {
      this.valueItem = (c.value as Term).id;
    }

    if (this.context.microType) {
      this.getUnits();
    } else {
      if (this.context.typeTerm) {
        // this code should be removed in the future as template context microtypes shoud ideally be provided in the JSON file
        // it is here to prevent fields from not being able to load units
        this.uploadService.searchPropertyMicroTypes(this.context.typeTerm.text)
          .subscribe((data: any) => {

            // get results from API call and find microtype from there
            const typeData = data.results.find(item => item.id === this.context.typeTerm.id);

            // if we still cant find the microtype after the API call, set the units to null
            if (!typeData) {
              this.context.units = null as Term;
            } else {
              this.context.microType = typeData.microtype;
              this.getUnits();
            }
          });
      }
    }
  }

  get context() { return this._context; }

  @Output() resetContext: EventEmitter<Context> = new EventEmitter();
  @Output() deleted: EventEmitter<any> = new EventEmitter();
  @Output() valueError: EventEmitter<any> = new EventEmitter();
  errorSub: Subscription;

  typesOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term) {
        options.callback({results: []});
      } else {
        this.uploadService.searchPropertyMicroTypes(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

   valuesOptions: Select2Options = {
     width: '100%',
     containerCssClass: 'select2-custom-container',
     query: (options: Select2QueryOptions) => {
       const term = options.term;
       if (!term) {
         options.callback({results: []});
       } else {
          if (this.context.scalarType === 'oterm_ref') {
            this.uploadService.searchOntPropertyValues(term, this.context.microType)
            .subscribe((data: any) => {
              options.callback({results: data.results as Select2OptionData});
            });
          } else {
            // scalar type is object_ref
            this.uploadService.searchPropertyValueObjectRefs(term, this.context.type.id, this.context.microType)
              .subscribe((data: any) => {
                options.callback({results: data.results as Select2OptionData});
              });
          }
       }
     }
   };

  unitsOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
   };

  public typesSelect2: Select2OptionData[];
  public unitsSelect2: Select2OptionData[];
  public valuesSelect2: Select2OptionData[];

  typeItem: string;
  unitsItem: string;
  valueItem: string;
  error = false;
  scalarError = false;

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
  ) { }

  ngOnInit() {
    this.errorSub = this.validator.getContextValidationErrors()
      .subscribe(error => this.error = error);
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  getUnits() {
    this.uploadService.searchOntPropertyUnits(this.context.microType)
    .subscribe(data => {
      if (!data.results.length) {
        this.context.units = null as Term;
      } else {
        if (this.context.units === null) {
          this.context.units = undefined;
        }
        this.unitsSelect2 = [...this.unitsSelect2, ...data.results];
      }
  });
  }

  setContextType(event) {
    const item = event.data[0];
    this.context.typeTerm = item;

    // clear reset entire property object to clear other select 2 dropdowns
    if (this.context.value || this.context.units) {
      const resetProperty = new Context(
        this.context.required,
        item
      );
      // emit new typed property to replace old one in parent component array reference
      this.resetContext.emit(resetProperty);
    } else {
      this.getUnits();
    }
  }

  setValue(event) {
    const item = event.data[0];
    this.context.value = new Term(item.id, item.text);
  }

  setUnits(event) {
    if (event.value.length) {
      const item = event.data[0];
      this.context.units = new Term(item.id, item.text);
    }
  }

  validateValue() {
    if (!this.validator.validScalarType(this.context.scalarType, this.context.value)) {
      this.scalarError = true;
      this.context.invalidValue = true;
      this.valueError.emit(this.validator.INVALID_VALUE);
    } else {
      this.scalarError = false;
      this.context.invalidValue = false;
      this.valueError.emit(null);
    }
  }

  onDelete() {
    this.deleted.emit();
  }

}
