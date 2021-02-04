import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { FormsModule } from '@angular/forms';
import { ModalModule } from 'ngx-bootstrap/modal';
import { BsDatepickerModule } from 'ngx-bootstrap/datepicker';
import { CreateComponent } from './create.component';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, Term } from 'src/app/shared/models/brick';
import { Subject } from 'rxjs';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { of, asyncScheduler } from 'rxjs';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { By } from '@angular/platform-browser';
import { NgSelectModule } from '@ng-select/ng-select';
const metadata = require('src/app/shared/test/brick-type-templates.json');

describe('CreateComponent', () => {
  let spectator: Spectator<CreateComponent>;

  const brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);

  const UploadServiceMock = {
    getBrickBuilder: () => brick,
    getProcessOterms: () => of({
      results: [{id: 'process0000', text: 'test process'}]
    }, asyncScheduler),
    getCampaignOterms: () => of({
      results: [{id: 'campaign0000', text: 'test campaign'}]
    }, asyncScheduler), 
    getPersonnelOterms: () => of({
      results: [{id: 'personnel0000', text: 'test personnel'}]
    }, asyncScheduler),
    requiredProcess: false,
    submitBrick: () => of({results: 'successID'}, asyncScheduler)
  };

  const mockValidationResult = {
    messages: [],
    startDateError: false,
    endDateError: false
  }

  const MockValidator = {
    validateCreateStep: () => mockValidationResult
  }

  const createComponent = createComponentFactory({
    component: CreateComponent,
    imports: [
      FormsModule,
      NgSelectModule,
      ModalModule.forRoot(),
      BsDatepickerModule.forRoot(),
      NgxSpinnerModule,
      HttpClientModule
    ],
    providers: [
      mockProvider(UploadService, UploadServiceMock),
      mockProvider(UploadValidationService, MockValidator)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should call to get processes', fakeAsync(() => {
    spectator.detectChanges();
    const uploadService = spectator.get(UploadService)
    spyOn(spectator.component, 'getProcessOterms').and.callThrough();
    spyOn(uploadService, 'getProcessOterms').and.callThrough();
    spectator.component.ngOnInit();

    spectator.detectChanges();
    expect(spectator.component.requiredProcess).toBeFalsy();
    tick();
    expect(spectator.component.getProcessOterms).toHaveBeenCalled();
    expect(uploadService.getProcessOterms).toHaveBeenCalled();
    expect(spectator.component.processData[0].id).toEqual('process0000');
    expect(spectator.component.processData[0].text).toEqual('test process')
  }));

  it('should call to get campaigns', fakeAsync(() => {
    spectator.detectChanges();
    const uploadService = spectator.get(UploadService);
    spyOn(spectator.component, 'getCampaignOterms').and.callThrough();
    spyOn(uploadService, 'getCampaignOterms').and.callThrough();
    spectator.component.ngOnInit();

    spectator.detectChanges();
    tick();
    expect(spectator.component.getCampaignOterms).toHaveBeenCalled();
    expect(uploadService.getCampaignOterms).toHaveBeenCalled();
    expect(spectator.component.campaignData[0].id).toBe('campaign0000');
    expect(spectator.component.campaignData[0].text).toBe('test campaign');
  }));

  it('should call to get personnel', fakeAsync(() => {
    spectator.detectChanges();
    const uploadService = spectator.get(UploadService);
    spyOn(spectator.component, 'getPersonnelOterms').and.callThrough();
    spyOn(uploadService, 'getPersonnelOterms').and.callThrough();
    spectator.component.ngOnInit();
    
    spectator.detectChanges();
    tick();
    expect(spectator.component.getPersonnelOterms).toHaveBeenCalled();
    expect(uploadService.getPersonnelOterms).toHaveBeenCalled();
    expect(spectator.component.personnelData[0].id).toBe('personnel0000');
    expect(spectator.component.personnelData[0].text).toBe('test personnel');
  }));

  it('should set process item to brick', () => {
    spyOn(spectator.component, 'setBrickProcess').and.callThrough();
    spectator.triggerEventHandler('ng-select#brick-process', 'change', {
      id: 'process0000',
      text: 'test process',
      has_units: false
    });
    spectator.detectChanges();
    expect(spectator.component.setBrickProcess).toHaveBeenCalled();
    expect(spectator.component.brick.process.text).toBe('test process');
    expect(spectator.component.brick.process.id).toBe('process0000');
  });

  it('should set cammpaign item to brick', () => {
    spyOn(spectator.component, 'setBrickCampaign').and.callThrough();
    spectator.triggerEventHandler('ng-select#brick-campaign', 'change', {
      id: 'campaign0000',
      text: 'test campaign',
      has_units: false
    });
    spectator.detectChanges();
    expect(spectator.component.setBrickCampaign).toHaveBeenCalled();
    expect(spectator.component.brick.campaign.text).toBe('test campaign');
    expect(spectator.component.brick.campaign.id).toBe('campaign0000');
  });

  it('should set personnel item to brick', () => {
    spyOn(spectator.component, 'setBrickPersonnel').and.callThrough();
    spectator.triggerEventHandler('ng-select#brick-personnel', 'change', {
      id: 'personnel0000',
      text: 'test personnel',
      has_units: false
    });
    spectator.detectChanges();
    expect(spectator.component.setBrickPersonnel).toHaveBeenCalled();
    expect(spectator.component.brick.personnel.text).toBe('test personnel');
    expect(spectator.component.brick.personnel.id).toBe('personnel0000');
  });

  it('should submit brick', fakeAsync(() => {
    const uploadService = spectator.get(UploadService);
    spyOn(spectator.component, 'submitBrick').and.callThrough();
    spyOn(uploadService, 'submitBrick').and.callThrough();
    spectator.click('button#submit-brick');
    spectator.detectChanges();

    expect(spectator.component.submitBrick).toHaveBeenCalled();
    expect(uploadService.submitBrick).toHaveBeenCalled();
    tick();
    spectator.detectChanges();

    expect(spectator.component.successId).toBe('successID');
    expect(spectator.query('button#submit-brick')).toBeDisabled();
    expect(spectator.query('div#success-banner')).not.toBeNull();
    const anchor = spectator.debugElement.query(By.css('a#success-link'));
    expect(anchor.nativeElement.getAttribute('href')).toBe('/search/result/brick/successID');

    // set validator to check for errors
    mockValidationResult.messages.push('test error message');
    mockValidationResult.endDateError = true;
    mockValidationResult.startDateError = true;
  }));

  it('should not submit if there are errors', () => {
    const uploadService = spectator.get(UploadService);
    spyOn(spectator.component, 'submitBrick').and.callThrough();
    spyOn(uploadService, 'submitBrick');
    spectator.click('button#submit-brick');
    spectator.detectChanges();

    expect(spectator.component.submitBrick).toHaveBeenCalled();
    expect(uploadService.submitBrick).not.toHaveBeenCalled();
    expect(spectator.component.error).toBeTruthy();
    expect(spectator.component.errorMessages).toHaveLength(1);

    expect(spectator.query('div.alert.alert-danger')).not.toBeNull();
    expect(spectator.query('div.alert.alert-danger')).toHaveText('test error message');
    expect(spectator.query('input#start-date')).toHaveClass('button-error');
    expect(spectator.query('input#end-date')).toHaveClass('button-error');
    expect(spectator.query('input#brick-name')).toHaveClass('button-error');
    expect(spectator.query('input#brick-description')).toHaveClass('button-error');
  });
});
